import React, { Fragment, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  Col,
  FormGroup,
  Input,
  Label,
  Row,
  Table,
} from "reactstrap";
import Swal from "sweetalert2";
import { H3 } from "../../../../../AbstractElements";
import {
  createManualTradePreview,
  executeManualTradeBatch,
  getGroupServicesList,
  getManualTradeBatch,
  getManualTradeBatches,
} from "../../../../../Services/Authentication";

const ACTIONS = [
  { value: "BUY_CE", label: "BUY CE" },
  { value: "BUY_PE", label: "BUY PE" },
];

const RESULT_FILTERS = [
  { value: "ALL", label: "All" },
  { value: "SUCCESS", label: "Success" },
  { value: "FAILED", label: "Failed" },
];

const statusColor = (status) => {
  const value = String(status || "").toUpperCase();
  if (["SUCCESS", "COMPLETED"].includes(value)) return "success";
  if (["FAILED"].includes(value)) return "danger";
  if (["PARTIAL"].includes(value)) return "warning";
  if (["QUEUED", "PROCESSING", "PENDING"].includes(value)) return "info";
  if (["SKIPPED"].includes(value)) return "secondary";
  return "primary";
};

const clientName = (result) => result?.client_name || result?.email || `Client #${result?.client_id || ""}`;

const extractScripts = (groupService) => {
  const rows = Array.isArray(groupService?.json_data) ? groupService.json_data : [];
  return Array.from(
    new Set(
      rows
        .map((row) => String(row?.ScriptName || row?.ServiceName || row?.script_name || "").trim().toUpperCase())
        .filter(Boolean)
    )
  );
};

const ManualTrade = () => {
  const navigate = useNavigate();
  const [groupServices, setGroupServices] = useState([]);
  const [batches, setBatches] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [symbol, setSymbol] = useState("");
  const [action, setAction] = useState("BUY_CE");
  const [strikePrice, setStrikePrice] = useState("");
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [selectedClientIds, setSelectedClientIds] = useState([]);
  const [resultStatusFilter, setResultStatusFilter] = useState("ALL");

  const selectedGroup = useMemo(
    () => groupServices.find((item) => String(item.id) === String(selectedGroupId)),
    [groupServices, selectedGroupId]
  );
  const scriptOptions = useMemo(() => extractScripts(selectedGroup), [selectedGroup]);
  const selectableResults = useMemo(
    () => (preview?.results || []).filter((result) => result.status === "PENDING"),
    [preview]
  );
  const allSelectableSelected = selectableResults.length > 0 && selectedClientIds.length === selectableResults.length;
  const filteredResults = useMemo(() => {
    const results = preview?.results || [];
    if (resultStatusFilter === "ALL") return results;
    return results.filter((result) => String(result.status || "").toUpperCase() === resultStatusFilter);
  }, [preview, resultStatusFilter]);

  const loadInitialData = async () => {
    const [groupsResult, batchesResult] = await Promise.allSettled([
      getGroupServicesList(),
      getManualTradeBatches(1, 10),
    ]);

    if (groupsResult.status === "fulfilled") {
      const groupPayload = groupsResult.value;
      setGroupServices(Array.isArray(groupPayload) ? groupPayload : groupPayload?.results || []);
    } else {
      setGroupServices([]);
      Swal.fire("Error", groupsResult.reason?.message || "Failed to fetch group services.", "error");
    }

    if (batchesResult.status === "fulfilled") {
      setBatches(batchesResult.value?.results || []);
    } else {
      setBatches([]);
      console.error("Failed to fetch trade execution batches:", batchesResult.reason);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (scriptOptions.length && !scriptOptions.includes(symbol)) {
      setSymbol(scriptOptions[0]);
    }
  }, [scriptOptions, symbol]);

  useEffect(() => {
    if (!preview?.id || !["QUEUED", "PROCESSING"].includes(preview.status)) return undefined;
    const intervalId = window.setInterval(async () => {
      try {
        const nextPreview = await getManualTradeBatch(preview.id);
        setPreview(nextPreview);
        if (!["QUEUED", "PROCESSING"].includes(nextPreview.status)) {
          window.clearInterval(intervalId);
          loadInitialData();
        }
      } catch (error) {
        window.clearInterval(intervalId);
      }
    }, 4000);
    return () => window.clearInterval(intervalId);
  }, [preview?.id, preview?.status]);

  const handlePreview = async () => {
    if (!selectedGroupId || !symbol || !strikePrice) {
      Swal.fire("Missing details", "Select group service, script and strike price.", "warning");
      return;
    }
    setLoading(true);
    try {
      const response = await createManualTradePreview({
        group_service_id: selectedGroupId,
        symbol,
        action,
        strike_price: strikePrice,
      });
      setPreview(response);
      setResultStatusFilter("ALL");
      setSelectedClientIds(
        (response.results || []).filter((result) => result.status === "PENDING").map((result) => result.client_id)
      );
      await loadInitialData();
    } catch (error) {
      Swal.fire("Error", error.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!preview?.id || selectedClientIds.length <= 0) {
      Swal.fire("Select clients", "Select at least one eligible client for this trade.", "warning");
      return;
    }

    setExecuting(true);
    try {
      const response = await executeManualTradeBatch(preview.id, selectedClientIds);
      setPreview(response);
      await loadInitialData();
      navigate("/tradedetails/orders", {
        state: {
          refreshAfterTradeExecution: true,
          tradeExecutionBatchId: preview.id,
        },
      });
    } catch (error) {
      Swal.fire("Error", error.message, "error");
    } finally {
      setExecuting(false);
    }
  };

  const openBatch = async (batchId) => {
    try {
      const response = await getManualTradeBatch(batchId);
      setPreview(response);
      setResultStatusFilter("ALL");
      setSelectedClientIds(
        response.status === "PREVIEW"
          ? (response.results || []).filter((result) => result.status === "PENDING").map((result) => result.client_id)
          : []
      );
    } catch (error) {
      Swal.fire("Error", error.message, "error");
    }
  };

  const toggleAllClients = () => {
    setSelectedClientIds(
      allSelectableSelected
        ? []
        : selectableResults.map((result) => result.client_id)
    );
  };

  return (
    <Fragment>
      <Col sm="12">
        <Card>
          <CardHeader>
            <H3>Trade Execution</H3>
          </CardHeader>
          <CardBody>
            <Row className="g-3 align-items-end">
              <Col md="3">
                <FormGroup>
                  <Label>Group Service</Label>
                  <Input type="select" value={selectedGroupId} onChange={(event) => setSelectedGroupId(event.target.value)}>
                    <option value="">Select Group Service</option>
                    {groupServices.map((group) => (
                      <option key={group.id} value={group.id}>{group.group_name}</option>
                    ))}
                  </Input>
                </FormGroup>
              </Col>
              <Col md="2">
                <FormGroup>
                  <Label>Script</Label>
                  {scriptOptions.length ? (
                    <Input type="select" value={symbol} onChange={(event) => setSymbol(event.target.value)}>
                      {scriptOptions.map((item) => (
                        <option key={item} value={item}>{item}</option>
                      ))}
                    </Input>
                  ) : (
                    <Input value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} placeholder="NIFTY" />
                  )}
                </FormGroup>
              </Col>
              <Col md="2">
                <FormGroup>
                  <Label>Action</Label>
                  <Input type="select" value={action} onChange={(event) => setAction(event.target.value)}>
                    {ACTIONS.map((item) => (
                      <option key={item.value} value={item.value}>{item.label}</option>
                    ))}
                  </Input>
                </FormGroup>
              </Col>
              <Col md="2">
                <FormGroup>
                  <Label>Strike Price</Label>
                  <Input type="number" value={strikePrice} onChange={(event) => setStrikePrice(event.target.value)} placeholder="22900" />
                </FormGroup>
              </Col>
              <Col md="3">
                <Button color="primary" disabled={loading} onClick={handlePreview}>
                  {loading ? "Creating Preview..." : "Preview Trade"}
                </Button>
              </Col>
            </Row>
          </CardBody>
        </Card>
      </Col>

      {preview && (
        <Col sm="12">
          <Card>
            <CardHeader className="d-flex justify-content-between align-items-center">
              <div>
                <H3>Preview</H3>
                <div>
                  <Badge color={statusColor(preview.status)}>{preview.status}</Badge>{" "}
                  {preview.group_service_name} - {preview.symbol} {preview.strike_price} {preview.action}
                </div>
              </div>
              <Button color="success" disabled={executing || preview.status !== "PREVIEW" || selectedClientIds.length <= 0} onClick={handleExecute}>
                {executing ? "Queuing..." : `Execute for ${selectedClientIds.length} Client(s)`}
              </Button>
            </CardHeader>
            <CardBody>
              <Row className="mb-3">
                <Col md="3"><strong>Total:</strong> {preview.preview_count}</Col>
                <Col md="3"><strong>Eligible:</strong> {preview.eligible_count}</Col>
                <Col md="3"><strong>Skipped:</strong> {preview.skipped_count}</Col>
                <Col md="3"><strong>Success/Failed:</strong> {preview.success_count}/{preview.failed_count}</Col>
              </Row>
              {preview.status === "PREVIEW" && preview.eligible_count > 0 && (
                <div className="mb-3">
                  <strong>{selectedClientIds.length} client(s) selected</strong>
                </div>
              )}
              {preview.status !== "PREVIEW" && (
                <Row className="mb-3 align-items-end">
                  <Col md="4" lg="3">
                    <FormGroup className="mb-0">
                      <Label for="tradeResultStatus">Filter Client Results</Label>
                      <Input
                        type="select"
                        id="tradeResultStatus"
                        value={resultStatusFilter}
                        onChange={(event) => setResultStatusFilter(event.target.value)}
                      >
                        {RESULT_FILTERS.map((filter) => (
                          <option key={filter.value} value={filter.value}>
                            {filter.label}
                            {filter.value === "SUCCESS" ? ` (${preview.success_count || 0})` : ""}
                            {filter.value === "FAILED" ? ` (${preview.failed_count || 0})` : ""}
                          </option>
                        ))}
                      </Input>
                    </FormGroup>
                  </Col>
                </Row>
              )}
              <div className="table-responsive">
                <Table bordered hover>
                  <thead>
                    <tr>
                      {preview.status === "PREVIEW" && (
                        <th style={{ width: "48px" }}>
                          <Input
                            type="checkbox"
                            className="trade-execution-client-checkbox"
                            aria-label="Select all clients"
                            checked={allSelectableSelected}
                            disabled={selectableResults.length === 0}
                            onChange={toggleAllClients}
                          />
                        </th>
                      )}
                      <th>Client</th>
                      <th>Broker</th>
                      <th>Expiry</th>
                      <th>Order</th>
                      <th>Qty</th>
                      <th>Status</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredResults.map((result) => (
                      <tr key={result.id}>
                        {preview.status === "PREVIEW" && (
                          <td className="text-center">
                            <Input
                              type="checkbox"
                              className="trade-execution-client-checkbox"
                              aria-label={`Select ${clientName(result)}`}
                              disabled={result.status !== "PENDING"}
                              checked={selectedClientIds.includes(result.client_id)}
                              onChange={(event) => setSelectedClientIds((current) => (
                                event.target.checked
                                  ? Array.from(new Set([...current, result.client_id]))
                                  : current.filter((clientId) => clientId !== result.client_id)
                              ))}
                            />
                          </td>
                        )}
                        <td>{clientName(result)}<br /><small>{result.email}</small></td>
                        <td>{result.broker || "-"}</td>
                        <td>{result.request_snapshot?.expiry_date || "-"}</td>
                        <td>{result.request_snapshot?.order_type || "-"} / {result.request_snapshot?.product_type || "-"}</td>
                        <td>{result.request_snapshot?.quantity || "-"}</td>
                        <td><Badge color={statusColor(result.status)}>{result.status}</Badge></td>
                        <td>{result.reason || "-"}</td>
                      </tr>
                    ))}
                    {!filteredResults.length && (
                      <tr>
                        <td colSpan={preview.status === "PREVIEW" ? 9 : 8} className="text-center">
                          No {resultStatusFilter === "ALL" ? "client" : resultStatusFilter.toLowerCase()} results found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </Table>
              </div>
            </CardBody>
          </Card>
        </Col>
      )}

      <Col sm="12">
        <Card>
          <CardHeader>
            <H3>Recent Trade Executions</H3>
          </CardHeader>
          <CardBody>
            <div className="table-responsive">
              <Table hover>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Group Service</th>
                    <th>Contract</th>
                    <th>Status</th>
                    <th>Eligible</th>
                    <th>Success</th>
                    <th>Failed</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {batches.map((batch) => (
                    <tr key={batch.id}>
                      <td>{batch.id}</td>
                      <td>{batch.group_service_name}</td>
                      <td>{batch.symbol} {batch.strike_price} {batch.action}</td>
                      <td><Badge color={statusColor(batch.status)}>{batch.status}</Badge></td>
                      <td>{batch.eligible_count}</td>
                      <td>{batch.success_count}</td>
                      <td>{batch.failed_count}</td>
                      <td><Button size="sm" color="primary" outline onClick={() => openBatch(batch.id)}>View</Button></td>
                    </tr>
                  ))}
                  {!batches.length && (
                    <tr>
                      <td colSpan="8" className="text-center">No trade executions found</td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};

export default ManualTrade;
