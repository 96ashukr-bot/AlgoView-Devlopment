import React, { Fragment, useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Col,
  Input,
  Pagination,
  PaginationItem,
  PaginationLink,
  Row,
  Table,
} from "reactstrap";
import { RotatingLines } from "react-loader-spinner";
import { H3 } from "../../../../AbstractElements";
import { getSLTPWatcherStatus } from "../../../../Services/Authentication";
import "./TradeDetails.css";

const badgeColorByStatus = {
  monitoring: "primary",
  triggered: "warning",
  skipped: "secondary",
  failed: "danger",
};

const formatNumber = (value) => {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return value;
  }
  return numericValue.toFixed(2);
};

const SLTPWatcher = () => {
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState({
    total: 0,
    monitoring: 0,
    triggered: 0,
    skipped: 0,
    failed: 0,
  });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    clientId: "",
    historyId: "",
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const fetchWatcherStatus = async (appliedFilters = filters) => {
    setLoading(true);
    try {
      const response = await getSLTPWatcherStatus({
        client_id: appliedFilters.clientId || undefined,
        history_id: appliedFilters.historyId || undefined,
      });
      setItems(response.results || []);
      setSummary(
        response.summary || {
          total: 0,
          monitoring: 0,
          triggered: 0,
          skipped: 0,
          failed: 0,
        }
      );
      setCurrentPage(1);
    } catch (error) {
      console.error("Failed to fetch SL/TP watcher status:", error);
      setItems([]);
      setSummary({
        total: 0,
        monitoring: 0,
        triggered: 0,
        skipped: 0,
        failed: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWatcherStatus();
  }, []);

  const filteredItems = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      return items;
    }

    return items.filter((item) => {
      const haystack = [
        item.client_name,
        item.group_service,
        item.script_name,
        item.symbol,
        item.trading_symbol,
        item.broker,
        item.status,
        item.trigger_reason,
        item.message,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return haystack.includes(query);
    });
  }, [items, searchQuery]);

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredItems.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage) || 1;

  const handleFilterChange = (event) => {
    const { name, value } = event.target;
    setFilters((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleApplyFilters = () => {
    fetchWatcherStatus(filters);
  };

  const handleReset = () => {
    const resetFilters = { clientId: "", historyId: "" };
    setFilters(resetFilters);
    setSearchQuery("");
    fetchWatcherStatus(resetFilters);
  };

  return (
    <Fragment>
      <Col sm="12">
        <Card>
          <CardHeader>
            <div className="d-flex justify-content-between align-items-center custom-responsive-style">
              <div>
                <H3>SL/TP Watcher</H3>
              </div>
              <div className="d-flex gap-2 flex-wrap">
                <Badge color="light-primary" pill>
                  Monitoring: {summary.monitoring}
                </Badge>
                <Badge color="light-warning" pill>
                  Triggered: {summary.triggered}
                </Badge>
                <Badge color="light-secondary" pill>
                  Skipped: {summary.skipped}
                </Badge>
                <Badge color="light-danger" pill>
                  Failed: {summary.failed}
                </Badge>
                <Badge color="light-success" pill>
                  Total: {summary.total}
                </Badge>
              </div>
            </div>
          </CardHeader>

          <div className="card-block row">
            <Col sm="12">
              <Row className="g-3 p-3">
                <Col md="2">
                  <Input
                    type="text"
                    name="clientId"
                    value={filters.clientId}
                    onChange={handleFilterChange}
                    placeholder="Client ID"
                  />
                </Col>
                <Col md="2">
                  <Input
                    type="text"
                    name="historyId"
                    value={filters.historyId}
                    onChange={handleFilterChange}
                    placeholder="History ID"
                  />
                </Col>
                <Col md="3">
                  <Input
                    type="text"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Search trades"
                  />
                </Col>
                <Col md="5" className="d-flex gap-2 flex-wrap">
                  <Button className="search-btn-clr" onClick={handleApplyFilters}>
                    Check
                  </Button>
                  <Button color="light" onClick={handleReset}>
                    Reset
                  </Button>
                  <Button color="primary" outline onClick={() => fetchWatcherStatus(filters)}>
                    Refresh
                  </Button>
                </Col>
              </Row>

              <div className="table-responsive-sm">
                <Table>
                  <thead>
                    <tr>
                      <th className="custom-col-design">S.No.</th>
                      <th className="custom-col-design">Status</th>
                      <th className="custom-col-design">Client</th>
                      <th className="custom-col-design">Group Service</th>
                      <th className="custom-col-design">Script</th>
                      <th className="custom-col-design">Trading Symbol</th>
                      <th className="custom-col-design">Broker</th>
                      <th className="custom-col-design">Qty</th>
                      <th className="custom-col-design">Entry Price</th>
                      <th className="custom-col-design">Current LTP</th>
                      <th className="custom-col-design">SL Price</th>
                      <th className="custom-col-design">Target Price</th>
                      <th className="custom-col-design">Trigger</th>
                      <th className="custom-col-design">Watcher Note</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan="14" style={{ textAlign: "center", height: "120px" }}>
                          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%" }}>
                            <RotatingLines
                              strokeColor="#283F7B"
                              strokeWidth="4"
                              animationDuration="0.75"
                              width="50"
                              visible
                            />
                          </div>
                        </td>
                      </tr>
                    ) : currentItems.length > 0 ? (
                      currentItems.map((item, index) => (
                        <tr key={item.trade_id}>
                          <td>{indexOfFirstItem + index + 1}</td>
                          <td>
                            <Badge color={badgeColorByStatus[item.status] || "dark"} pill>
                              {item.status || "-"}
                            </Badge>
                          </td>
                          <td>
                            {item.client_name || "-"}
                            <br />
                            <small>ID: {item.client_id}</small>
                          </td>
                          <td>{item.group_service || "-"}</td>
                          <td>{item.script_name || item.symbol || "-"}</td>
                          <td>{item.trading_symbol || "-"}</td>
                          <td>{item.broker || "-"}</td>
                          <td>{item.quantity || "-"}</td>
                          <td>{formatNumber(item.entry_price)}</td>
                          <td>{formatNumber(item.current_ltp)}</td>
                          <td>{formatNumber(item.stop_loss_price)}</td>
                          <td>{formatNumber(item.target_price)}</td>
                          <td>{item.trigger_reason || "-"}</td>
                          <td style={{ minWidth: "260px" }}>{item.message || "-"}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="14" style={{ textAlign: "center", padding: "16px" }}>
                          No watched trades found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </Table>
              </div>

              <div className="d-flex justify-content-end align-items-center gap-2 custom-pagi-style p-3">
                <p className="mb-0 me-2">Rows per page</p>
                <Input
                  type="select"
                  value={itemsPerPage}
                  onChange={(event) => {
                    setItemsPerPage(parseInt(event.target.value, 10));
                    setCurrentPage(1);
                  }}
                  style={{ width: "80px" }}
                >
                  <option value="10">10</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                </Input>

                <Pagination>
                  <PaginationItem disabled={currentPage === 1}>
                    <PaginationLink onClick={() => setCurrentPage(currentPage - 1)}>
                      Previous
                    </PaginationLink>
                  </PaginationItem>
                  {Array.from({ length: totalPages }, (_, idx) => idx + 1).map((page) => (
                    <PaginationItem key={page} active={page === currentPage}>
                      <PaginationLink onClick={() => setCurrentPage(page)}>
                        {page}
                      </PaginationLink>
                    </PaginationItem>
                  ))}
                  <PaginationItem disabled={currentPage === totalPages}>
                    <PaginationLink onClick={() => setCurrentPage(currentPage + 1)}>
                      Next
                    </PaginationLink>
                  </PaginationItem>
                </Pagination>
              </div>
            </Col>
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};

export default SLTPWatcher;
