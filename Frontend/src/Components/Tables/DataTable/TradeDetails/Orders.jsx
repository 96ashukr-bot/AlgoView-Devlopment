import React, { Fragment, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Badge,
  Button,
  ButtonGroup,
  Card,
  CardBody,
  CardHeader,
  Col,
  Form,
  FormGroup,
  Input,
  Label,
  Modal,
  ModalBody,
  ModalHeader,
  Pagination,
  PaginationItem,
  PaginationLink,
  Row,
  Table,
} from "reactstrap";
import { RotatingLines } from "react-loader-spinner";
import { fetchUserProfile, forceKillSwitchSelectedTrades, getOrderFilterOptions, getOrders } from "../../../../Services/Authentication";
import { getSLTPWatcherLiveSocketUrl } from "../../../../ConfigUrl/config";
import { getAccessToken } from "../../../../Services/authStorage";
import { H3 } from "../../../../AbstractElements";
import { getTradeSymbolDisplay } from "../../../../Utils/tradeSymbolDisplay";
import Swal from "sweetalert2";
import { useLocation } from "react-router-dom";
import "./TradeDetails.css";

const ORDER_BUCKETS = [
  { value: "ACTIVE", label: "ACTIVE", color: "success" },
  { value: "CLOSED", label: "CLOSED", color: "primary" },
  { value: "FAILED", label: "FAILED", color: "danger" },
];

const staticIndexSymbols = ["BANKNIFTY", "NIFTY", "MIDCPNIFTY", "FINNIFTY", "SENSEX"];

const formatDateTime = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
};

const decimalOrNull = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const formatNumber = (value) => {
  const parsed = decimalOrNull(value);
  if (parsed === null) return "-";
  return parsed.toFixed(2);
};

const formatProfit = (value) => {
  const parsed = decimalOrNull(value) ?? 0;
  return parsed.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const calculatePnl = (order, useLivePrice = false) => {
  if (order?.Total !== null && order?.Total !== undefined && order?.Total !== "") {
    return order.Total;
  }
  const entryPrice = decimalOrNull(order?.Entry_Price);
  const exitPrice = useLivePrice
    ? decimalOrNull(order?.current_ltp ?? order?.LivePrice)
    : decimalOrNull(order?.Exit_Price);
  const qty = decimalOrNull(order?.ExitQty ?? order?.EntryQty);
  if (entryPrice === null || exitPrice === null || qty === null) return null;
  const entryType = String(order?.Entry_type || "").trim().toUpperCase();
  const pnl = ["SELL", "SHORT"].includes(entryType)
    ? (entryPrice - exitPrice) * qty
    : (exitPrice - entryPrice) * qty;
  return pnl.toFixed(2);
};

const getReasonText = (order) => {
  const reason = order?.failure_reason || order?.broker_response || order?.response_data || "";
  if (!reason) return "";
  if (typeof reason === "string") return reason;
  try {
    return JSON.stringify(reason, null, 2);
  } catch (error) {
    return String(reason);
  }
};

const isKillSwitchEligible = (order) => {
  const orderId = String(order?.order_id || "").trim();
  const orderStatus = String(order?.order_status || "").trim().toLowerCase();
  const tradeStatus = String(order?.trade_order_status || "").trim().toLowerCase();
  if (!orderId || orderId === "0") return false;
  if (["failed", "rejected", "errors", "error", "unauthorized", "cancelled", "canceled"].includes(orderStatus)) return false;
  if (["failed", "skipped", "close", "closed", "exit", "exited", "squareoff", "squared_off"].includes(tradeStatus)) return false;
  return true;
};

const Orders = () => {
  const location = useLocation();
  const [orders, setOrders] = useState([]);
  const [brokers, setBrokers] = useState([]);
  const [groupServices, setGroupServices] = useState([]);
  const [clients, setClients] = useState([]);
  const [isClientUser, setIsClientUser] = useState(false);
  const [orderBucket, setOrderBucket] = useState("ACTIVE");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [cumulativeProfit, setCumulativeProfit] = useState(null);
  const [overallRunningPnl, setOverallRunningPnl] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [killSwitchTradeIds, setKillSwitchTradeIds] = useState([]);
  const [selectedTradeIds, setSelectedTradeIds] = useState([]);
  const [reasonModal, setReasonModal] = useState({ open: false, content: "" });
  const socketRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const [formData, setFormData] = useState({
    fromDate: "",
    toDate: "",
    broker: "",
    indexSymbol: "",
    groupService: "",
    clientId: "",
  });

  const activeBucket = useMemo(
    () => ORDER_BUCKETS.find((bucket) => bucket.value === orderBucket) || ORDER_BUCKETS[0],
    [orderBucket]
  );
  const selectedClientName = useMemo(() => {
    if (!formData.clientId) return "All Closed Orders";
    const client = clients.find((row) => String(row.id) === String(formData.clientId));
    return client?.fullName || client?.full_name || client?.email || `Client #${formData.clientId}`;
  }, [clients, formData.clientId]);
  const showExitColumns = orderBucket !== "ACTIVE";
  const tableColumnCount = showExitColumns ? 13 : 14;
  const eligibleTradeIds = useMemo(
    () => orders.filter(isKillSwitchEligible).map((order) => order.id).filter(Boolean),
    [orders]
  );
  const visibleTradeIds = useMemo(
    () => orders.map((order) => order.id).filter(Boolean),
    [orders]
  );
  const visibleTradeIdsSignature = visibleTradeIds.join(",");
  const allEligibleSelected = eligibleTradeIds.length > 0 && eligibleTradeIds.every((id) => selectedTradeIds.includes(id));

  const fetchOrders = useCallback(async ({ silent = false } = {}) => {
    if (!silent) {
      setLoading(true);
      setCumulativeProfit(null);
      setOverallRunningPnl(null);
    }
    try {
      const response = await getOrders(
        currentPage,
        itemsPerPage,
        orderBucket,
        formData.fromDate,
        formData.toDate,
        formData.broker,
        formData.indexSymbol,
        formData.groupService,
        searchQuery,
        formData.clientId
      );
      const nextOrders = response?.results || [];
      setOrders(nextOrders);
      setCumulativeProfit(orderBucket === "CLOSED" ? decimalOrNull(response?.cumulative_profit) : null);
      setOverallRunningPnl(orderBucket === "ACTIVE" ? decimalOrNull(response?.overall_running_pnl) : null);
      if (silent) {
        const nextEligibleIds = new Set(
          nextOrders.filter(isKillSwitchEligible).map((order) => order.id).filter(Boolean)
        );
        setSelectedTradeIds((current) => current.filter((id) => nextEligibleIds.has(id)));
      } else {
        setSelectedTradeIds([]);
      }
      setTotalPages(Math.max(1, Math.ceil((response?.count || 0) / itemsPerPage)));
    } catch (error) {
      if (!silent) {
        setOrders([]);
        setCumulativeProfit(null);
        setOverallRunningPnl(null);
        setSelectedTradeIds([]);
        setTotalPages(1);
      }
      console.error("Failed to fetch orders:", error);
    } finally {
      if (!silent) setLoading(false);
    }
  }, [currentPage, itemsPerPage, orderBucket, formData.fromDate, formData.toDate, formData.broker, formData.indexSymbol, formData.groupService, formData.clientId, searchQuery]);

  const fetchFilterData = async () => {
    try {
      const profile = await fetchUserProfile();
      const roleName = String(profile?.role?.name || "").trim().toLowerCase();
      const clientUser = roleName === "client" || roleName === "user" || profile?.type_of_user === "is_client";
      setIsClientUser(clientUser);

      const options = await getOrderFilterOptions();
      setBrokers(options?.brokers || []);
      setGroupServices(options?.group_services || []);
      setClients(clientUser ? [] : options?.clients || []);
    } catch (error) {
      console.error("Failed to fetch order filter data:", error);
    }
  };

  useEffect(() => {
    fetchFilterData();
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  useEffect(() => {
    if (!location.state?.refreshAfterTradeExecution) return undefined;
    let refreshCount = 0;
    const intervalId = window.setInterval(() => {
      refreshCount += 1;
      fetchOrders({ silent: true });
      if (refreshCount >= 10) {
        window.clearInterval(intervalId);
      }
    }, 2000);
    return () => window.clearInterval(intervalId);
  }, [fetchOrders, location.state]);

  useEffect(() => {
    let disposed = false;
    let reconnectDelay = 1000;

    const connect = () => {
      const token = getAccessToken();
      if (!token || disposed) return;
      const socket = new window.WebSocket(getSLTPWatcherLiveSocketUrl());
      socketRef.current = socket;

      socket.onopen = () => {
        reconnectDelay = 1000;
        socket.send(JSON.stringify({
          type: "authenticate",
          token,
          client_id: formData.clientId || undefined,
          from_date: formData.fromDate || undefined,
          to_date: formData.toDate || undefined,
          broker: formData.broker || undefined,
          index_symbol: formData.indexSymbol || undefined,
          group_service: formData.groupService || undefined,
          search: searchQuery || undefined,
          trade_ids: visibleTradeIds,
        }));
      };
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === "price_ticks" && Array.isArray(message.ticks)) {
            const liveTotal = decimalOrNull(message.overall_running_pnl);
            if (liveTotal !== null) setOverallRunningPnl(liveTotal);
            const ticksByTrade = new Map(message.ticks.map((tick) => [tick.trade_id, tick]));
            setOrders((current) => current.map((order) => {
              const tick = ticksByTrade.get(order.id);
              return tick ? { ...order, current_ltp: tick.current_ltp } : order;
            }));
          }
        } catch (error) {
          console.error("Invalid Orders live-price message:", error);
        }
      };
      socket.onclose = () => {
        socketRef.current = null;
        if (!disposed) {
          reconnectTimerRef.current = window.setTimeout(connect, reconnectDelay);
          reconnectDelay = Math.min(reconnectDelay * 2, 15000);
        }
      };
      socket.onerror = () => socket.close();
    };

    if (orderBucket === "ACTIVE") {
      connect();
    }
    return () => {
      disposed = true;
      if (reconnectTimerRef.current) window.clearTimeout(reconnectTimerRef.current);
      if (socketRef.current) socketRef.current.close();
    };
  }, [orderBucket, formData.clientId, formData.fromDate, formData.toDate, formData.broker, formData.indexSymbol, formData.groupService, searchQuery, visibleTradeIdsSignature]);

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setCurrentPage(1);
    setFormData((current) => ({ ...current, [name]: value }));
  };

  const handleBucketChange = (bucket) => {
    setCurrentPage(1);
    setOrderBucket(bucket);
  };

  const handleReset = () => {
    setCurrentPage(1);
    setSearchQuery("");
    setOrderBucket("ACTIVE");
    setFormData({ fromDate: "", toDate: "", broker: "", indexSymbol: "", groupService: "", clientId: "" });
  };

  const handleSelectTrade = (tradeId, checked) => {
    setSelectedTradeIds((current) => {
      if (checked) {
        return current.includes(tradeId) ? current : [...current, tradeId];
      }
      return current.filter((id) => id !== tradeId);
    });
  };

  const handleSelectAllTrades = (checked) => {
    setSelectedTradeIds((current) => {
      if (!checked) {
        return current.filter((id) => !eligibleTradeIds.includes(id));
      }
      return Array.from(new Set([...current, ...eligibleTradeIds]));
    });
  };

  const handleOrderKillSwitch = async () => {
    const selectedEligibleIds = selectedTradeIds.filter((id) => eligibleTradeIds.includes(id));
    if (!selectedEligibleIds.length || killSwitchTradeIds.length) {
      if (!selectedEligibleIds.length) {
        Swal.fire("Select Trade", "Please select at least one active trade to square off.", "warning");
      }
      return;
    }

    setKillSwitchTradeIds(selectedEligibleIds);
    try {
      const response = await forceKillSwitchSelectedTrades({
        trade_history_ids: selectedEligibleIds,
        reason: "Orders selected kill switch",
        async: true,
      });
      setOrders((current) => current.filter((order) => !selectedEligibleIds.includes(order.id)));
      setSelectedTradeIds((current) => current.filter((id) => !selectedEligibleIds.includes(id)));
      window.setTimeout(() => {
        fetchOrders();
      }, 1200);
      const failedCount = response?.failed_count || 0;
      const queuedCount = response?.queued_count || 0;
      if (failedCount) {
        Swal.fire("Kill Switch Queued", `${queuedCount || response?.sent_count || 0} exit order(s) queued. ${failedCount} failed validation.`, "warning");
      } else {
        Swal.fire("Kill Switch Sent", `${queuedCount || selectedEligibleIds.length} exit order(s) queued for immediate square off.`, "success");
      }
    } catch (error) {
      Swal.fire("Error", error.message || "Failed to run kill switch.", "error");
    } finally {
      setKillSwitchTradeIds([]);
    }
  };

  const renderPagination = () => {
    const pages = Array.from({ length: totalPages }, (_, index) => index + 1).slice(
      Math.max(0, currentPage - 3),
      Math.max(5, currentPage + 2)
    );
    return (
      <Pagination>
        <PaginationItem disabled={currentPage === 1}>
          <PaginationLink previous onClick={() => setCurrentPage((page) => Math.max(1, page - 1))} />
        </PaginationItem>
        {pages.map((page) => (
          <PaginationItem active={page === currentPage} key={page}>
            <PaginationLink onClick={() => setCurrentPage(page)}>{page}</PaginationLink>
          </PaginationItem>
        ))}
        <PaginationItem disabled={currentPage === totalPages}>
          <PaginationLink next onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))} />
        </PaginationItem>
      </Pagination>
    );
  };

  return (
    <Fragment>
      <Col sm="12">
        <Card>
          <CardHeader>
            <div className="d-flex flex-wrap justify-content-between align-items-center gap-2">
              <H3>Orders</H3>
              <ButtonGroup>
                {ORDER_BUCKETS.map((bucket) => (
                  <Button
                    key={bucket.value}
                    color={bucket.color}
                    outline={orderBucket !== bucket.value}
                    onClick={() => handleBucketChange(bucket.value)}
                  >
                    {bucket.label}
                  </Button>
                ))}
              </ButtonGroup>
            </div>
            <Form className="mt-3">
              <Row className="orders-filter-row">
                {!isClientUser && (
                  <>
                    <Col className="orders-filter-item">
                      <FormGroup className="orders-filter-group">
                        <Label>From</Label>
                        <Input type="date" name="fromDate" value={formData.fromDate} onChange={handleInputChange} />
                      </FormGroup>
                    </Col>
                    <Col className="orders-filter-item">
                      <FormGroup className="orders-filter-group">
                        <Label>To</Label>
                        <Input type="date" name="toDate" value={formData.toDate} onChange={handleInputChange} />
                      </FormGroup>
                    </Col>
                  </>
                )}
                <Col className="orders-filter-item">
                  <FormGroup className="orders-filter-group">
                    <Label>Broker</Label>
                    <Input type="select" name="broker" value={formData.broker} onChange={handleInputChange}>
                      <option value="">All</option>
                      {brokers.map((broker) => (
                        <option key={broker.id || broker.broker_name} value={broker.broker_name}>{broker.broker_name}</option>
                      ))}
                    </Input>
                  </FormGroup>
                </Col>
                <Col className="orders-filter-item">
                  <FormGroup className="orders-filter-group">
                    <Label>Script</Label>
                    <Input type="select" name="indexSymbol" value={formData.indexSymbol} onChange={handleInputChange}>
                      <option value="">All</option>
                      {staticIndexSymbols.map((symbol) => (
                        <option key={symbol} value={symbol}>{symbol}</option>
                      ))}
                    </Input>
                  </FormGroup>
                </Col>
                <Col className="orders-filter-item orders-filter-item-wide">
                  <FormGroup className="orders-filter-group">
                    <Label>Group Service</Label>
                    <Input type="select" name="groupService" value={formData.groupService} onChange={handleInputChange}>
                      <option value="">All</option>
                      {groupServices.map((service) => {
                        const serviceName = service.group_name || service.name || service.group_service || service.GroupService || service;
                        return <option key={service.id || serviceName} value={serviceName}>{serviceName}</option>;
                      })}
                    </Input>
                  </FormGroup>
                </Col>
                {!isClientUser && (
                  <Col className="orders-filter-item orders-filter-item-wide">
                    <FormGroup className="orders-filter-group">
                      <Label>Client</Label>
                      <Input type="select" name="clientId" value={formData.clientId} onChange={handleInputChange}>
                        <option value="">All</option>
                        {clients.map((client) => (
                          <option key={client.id} value={client.id}>
                            {client.fullName || client.full_name || client.email || `Client #${client.id}`}
                          </option>
                        ))}
                      </Input>
                    </FormGroup>
                  </Col>
                )}
                <Col className="orders-filter-item orders-filter-search">
                  <FormGroup className="orders-filter-group">
                    <Label>Search</Label>
                    <Input
                      value={searchQuery}
                      onChange={(event) => {
                        setCurrentPage(1);
                        setSearchQuery(event.target.value);
                      }}
                      placeholder="Client, broker, symbol, group service or order id"
                    />
                  </FormGroup>
                </Col>
                <Col className="orders-filter-reset">
                  <Button className="search-btn-clr" onClick={handleReset}>Reset</Button>
                </Col>
              </Row>
            </Form>
          </CardHeader>
          <CardBody>
            <div className="mb-3 d-flex flex-wrap justify-content-between align-items-center gap-2">
              <Badge color={activeBucket.color}>{activeBucket.label}</Badge>
              {orderBucket === "CLOSED" && (
                <div className="fw-bold">
                  Overall Profit ({selectedClientName}):{" "}
                  <span style={{ color: (cumulativeProfit ?? 0) < 0 ? "red" : "green" }}>
                    ₹{formatProfit(cumulativeProfit)}
                  </span>
                </div>
              )}
              {orderBucket === "ACTIVE" && (
                <div className="fw-bold">
                  Overall Running P&amp;L: {" "}
                  <span style={{ color: (overallRunningPnl ?? 0) < 0 ? "red" : "green" }}>
                    ₹{formatProfit(overallRunningPnl)}
                  </span>
                </div>
              )}
              {!showExitColumns && (
                <Button
                  color="danger"
                  disabled={!selectedTradeIds.length || killSwitchTradeIds.length}
                  onClick={handleOrderKillSwitch}
                >
                  {killSwitchTradeIds.length ? "Exiting..." : `Kill Switch${selectedTradeIds.length ? ` (${selectedTradeIds.length})` : ""}`}
                </Button>
              )}
            </div>
            <div className="table-responsive">
              <Table responsive hover>
                <thead>
                  <tr>
                    {!showExitColumns && (
                      <th className="kill-switch-select-col">
                        <Input
                          type="checkbox"
                          className="orders-kill-switch-checkbox"
                          checked={allEligibleSelected}
                          disabled={!eligibleTradeIds.length || killSwitchTradeIds.length}
                          onChange={(event) => handleSelectAllTrades(event.target.checked)}
                        />
                      </th>
                    )}
                    <th>S.No.</th>
                    <th>Entry Time</th>
                    <th>Trading Symbol</th>
                    <th>Group Service</th>
                    <th>Broker</th>
                    <th>Qty</th>
                    <th>Buy Price</th>
                    {!showExitColumns && <th>SL</th>}
                    {!showExitColumns && <th>Price</th>}
                    {!showExitColumns && <th>TP</th>}
                    {showExitColumns && <th>Exit Time</th>}
                    {showExitColumns && <th>Exit Qty</th>}
                    {showExitColumns && <th>Exit Price</th>}
                    <th>P&amp;L</th>
                    <th>Client</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={tableColumnCount} className="text-center" style={{ height: 120 }}>
                        <RotatingLines strokeColor="#283F7B" strokeWidth="4" animationDuration="0.75" width="50" visible />
                      </td>
                    </tr>
                  ) : orders.length ? (
                    orders.map((order, index) => {
                      const pnl = calculatePnl(order, !showExitColumns);
                      const pnlValue = decimalOrNull(pnl);
                      return (
                        <tr key={order.id}>
                          {!showExitColumns && (
                            <td className="kill-switch-select-col">
                              <Input
                                type="checkbox"
                                className="orders-kill-switch-checkbox"
                                checked={selectedTradeIds.includes(order.id)}
                                disabled={!isKillSwitchEligible(order) || killSwitchTradeIds.includes(order.id)}
                                onChange={(event) => handleSelectTrade(order.id, event.target.checked)}
                              />
                            </td>
                          )}
                          <td>{(currentPage - 1) * itemsPerPage + index + 1}</td>
                          <td>{formatDateTime(order.SignalEntry_time)}</td>
                          <td>{getTradeSymbolDisplay(order)}</td>
                          <td>{order.GroupService || "-"}</td>
                          <td>{order.broker || "-"}</td>
                          <td>{order.EntryQty || "-"}</td>
                          <td>{order.Entry_Price ?? "-"}</td>
                          {!showExitColumns && <td>{formatNumber(order.stop_loss_price)}</td>}
                          {!showExitColumns && <td>{formatNumber(order.current_ltp ?? order.LivePrice)}</td>}
                          {!showExitColumns && <td>{formatNumber(order.target_price)}</td>}
                          {showExitColumns && <td>{formatDateTime(order.SignalExit_time)}</td>}
                          {showExitColumns && <td>{order.ExitQty || "-"}</td>}
                          {showExitColumns && <td>{order.Exit_Price ?? "-"}</td>}
                          <td style={{ color: pnlValue < 0 ? "red" : "green", fontWeight: 700 }}>{pnl ?? "-"}</td>
                          <td>{order.client?.full_name || order.client?.email || "-"}</td>
                          <td>
                            {getReasonText(order) ? (
                              <Button
                                color="primary"
                                outline
                                size="sm"
                                onClick={() => setReasonModal({ open: true, content: getReasonText(order) })}
                              >
                                View
                              </Button>
                            ) : "-"}
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={tableColumnCount} className="text-center">No {orderBucket.toLowerCase()} orders found</td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </div>
            <div className="d-flex flex-wrap justify-content-end align-items-center gap-2">
              <span>Rows per page</span>
              <Input
                type="select"
                value={itemsPerPage}
                onChange={(event) => {
                  setCurrentPage(1);
                  setItemsPerPage(Number(event.target.value));
                }}
                style={{ width: 90 }}
              >
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </Input>
              {renderPagination()}
            </div>
          </CardBody>
        </Card>
        <Modal isOpen={reasonModal.open} toggle={() => setReasonModal({ open: false, content: "" })} size="lg">
          <ModalHeader toggle={() => setReasonModal({ open: false, content: "" })}>Reason</ModalHeader>
          <ModalBody>
            <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0 }}>
              {reasonModal.content || "-"}
            </pre>
          </ModalBody>
        </Modal>
      </Col>
    </Fragment>
  );
};

export default Orders;
