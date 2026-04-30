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
import { getWebhookDiagnostics } from "../../../../Services/Authentication";
import "./TradeDetails.css";

const WebhookDiagnostics = () => {
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState({ total: 0, ready: 0, blocked: 0 });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    symbol: "",
    groupService: "",
    clientId: "",
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const fetchDiagnostics = async (appliedFilters = filters) => {
    setLoading(true);
    try {
      const response = await getWebhookDiagnostics({
        symbol: appliedFilters.symbol || undefined,
        group_service: appliedFilters.groupService || undefined,
        client_id: appliedFilters.clientId || undefined,
      });
      setItems(response.data || []);
      setSummary(response.summary || { total: 0, ready: 0, blocked: 0 });
      setCurrentPage(1);
    } catch (error) {
      console.error("Failed to fetch webhook diagnostics:", error);
      setItems([]);
      setSummary({ total: 0, ready: 0, blocked: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  const filteredItems = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      return items;
    }

    return items.filter((item) => {
      const haystack = [
        item.client_name,
        item.client_username,
        item.group_service,
        item.segment,
        item.script_name,
        item.trade_symbol,
        item.broker,
        item.status,
        ...(item.skip_reasons || []),
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
    fetchDiagnostics(filters);
  };

  const handleReset = () => {
    const resetFilters = { symbol: "", groupService: "", clientId: "" };
    setFilters(resetFilters);
    setSearchQuery("");
    fetchDiagnostics(resetFilters);
  };

  return (
    <Fragment>
      <Col sm="12">
        <Card>
          <CardHeader>
            <div className="d-flex justify-content-between align-items-center custom-responsive-style">
              <div>
                <H3>Webhook Diagnostics</H3>
              </div>
              <div className="d-flex gap-2 flex-wrap">
                <Badge color="light-success" pill>
                  Ready: {summary.ready}
                </Badge>
                <Badge color="light-danger" pill>
                  Blocked: {summary.blocked}
                </Badge>
                <Badge color="light-primary" pill>
                  Total: {summary.total}
                </Badge>
              </div>
            </div>
          </CardHeader>

          <div className="card-block row">
            <Col sm="12">
              <Row className="g-3 p-3">
                <Col md="3">
                  <Input
                    type="text"
                    name="symbol"
                    value={filters.symbol}
                    onChange={handleFilterChange}
                    placeholder="Script, e.g. NIFTY"
                  />
                </Col>
                <Col md="3">
                  <Input
                    type="text"
                    name="groupService"
                    value={filters.groupService}
                    onChange={handleFilterChange}
                    placeholder="Group Service, e.g. Lite"
                  />
                </Col>
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
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Search rows"
                  />
                </Col>
                <Col md="2" className="d-flex gap-2">
                  <Button className="search-btn-clr" onClick={handleApplyFilters}>
                    Check
                  </Button>
                  <Button color="light" onClick={handleReset}>
                    Reset
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
                      <th className="custom-col-design">Segment</th>
                      <th className="custom-col-design">Script</th>
                      <th className="custom-col-design">Broker</th>
                      <th className="custom-col-design">Product</th>
                      <th className="custom-col-design">Qty</th>
                      <th className="custom-col-design">Expiry</th>
                      <th className="custom-col-design">Reasons</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan="11" style={{ textAlign: "center", height: "120px" }}>
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
                        <tr key={item.trade_setting_id}>
                          <td>{indexOfFirstItem + index + 1}</td>
                          <td>
                            <Badge color={item.status === "ready" ? "success" : "danger"} pill>
                              {item.status === "ready" ? "Ready" : "Blocked"}
                            </Badge>
                          </td>
                          <td>
                            {item.client_name || "-"}
                            <br />
                            <small>ID: {item.client_id}</small>
                          </td>
                          <td>{item.group_service || "-"}</td>
                          <td>{item.segment || "-"}</td>
                          <td>{item.script_name || item.trade_symbol || "-"}</td>
                          <td>{item.broker || "-"}</td>
                          <td>{item.product_type || "-"}</td>
                          <td>{item.quantity || "-"}</td>
                          <td>{item.expiry_date ? new Date(item.expiry_date).toLocaleString() : "-"}</td>
                          <td style={{ minWidth: "260px" }}>
                            {item.skip_reasons && item.skip_reasons.length > 0 ? (
                              item.skip_reasons.map((reason, reasonIndex) => (
                                <div key={`${item.trade_setting_id}-${reasonIndex}`}>{reason}</div>
                              ))
                            ) : (
                              <span>No blocking issues</span>
                            )}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="11" style={{ textAlign: "center", padding: "16px" }}>
                          No diagnostics found
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

export default WebhookDiagnostics;
