import React, { useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, CardBody, Col, Input, Label, Row, Table } from "reactstrap";
import Swal from "sweetalert2";
import {
  executeMultiLegStrategy,
  exitMultiLegStrategy,
  getActiveMultiLegStrategies,
  getClientMultiLegSettings,
  getExpiryDate,
  getSpecificDetails,
  getMultiLegStrategyDetail,
  getMultiLegStrategyLogs,
  killSwitchMultiLegStrategies,
} from "../../../Services/Authentication";

const STRATEGY_OPTIONS = [
  { value: "SHORT_STRADDLE", label: "Short Straddle" },
  { value: "BULL_CALL_SPREAD", label: "Bull Call Spread" },
  { value: "BEAR_CALL_SPREAD", label: "Bear Call Spread" },
  { value: "BEAR_PUT_SPREAD", label: "Bear Put Spread" },
  { value: "LONG_CALL_BUTTERFLY", label: "Long Call Butterfly" },
  { value: "SHORT_CALL_BUTTERFLY", label: "Short Call Butterfly" },
  { value: "LONG_CALL_CONDOR", label: "Long Call Condor" },
  { value: "SHORT_CALL_CONDOR", label: "Short Call Condor" },
  { value: "LONG_IRON_CONDOR", label: "Long Iron Condor" },
  { value: "SHORT_IRON_BUTTERFLY", label: "Short Iron Butterfly" },
];

const DEFAULT_FORM = {
  client_id: "",
  broker: "Angel One",
  strategy_name: "BULL_CALL_SPREAD",
  underlying: "NIFTY",
  expiry: "nearest",
  lower_strike: "",
  higher_strike: "",
  quantity_lots: 1,
  order_type: "LIMIT",
  product_type: "INTRADAY",
  buffer_percentage: 0.5,
  sell_leg_stop_loss_percentage: 40,
  combined_trailing_start: 1000,
  combined_trailing_gap: 500,
  entry_time: "09:30",
  exit_time: "15:15",
  allow_reentry: false,
};

const UNDERLYING_OPTIONS = ["NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY"];
const EXPIRY_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

const formatExpiryForDropdown = (value) => {
  const rawValue = String(value || "").trim().toUpperCase();
  if (!rawValue || rawValue === "NEAREST") {
    return rawValue ? "nearest" : "";
  }
  if (/^\d{2}[A-Z]{3}\d{4}$/.test(rawValue)) {
    return rawValue;
  }
  const datePart = rawValue.split("T")[0];
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(datePart);
  if (!match) {
    return rawValue;
  }
  const [, year, month, day] = match;
  return `${day}${EXPIRY_MONTHS[Number(month) - 1]}${year}`;
};

const statusColor = (status) => {
  switch (status) {
    case "ACTIVE":
      return "success";
    case "EXITED":
      return "secondary";
    case "FAILED":
      return "danger";
    case "ROLLED_BACK":
      return "warning";
    case "EXECUTING":
    case "EXITING":
      return "info";
    default:
      return "primary";
  }
};

const MultiLegExecutionPage = () => {
  const [formData, setFormData] = useState(DEFAULT_FORM);
  const [brokerNames, setBrokerNames] = useState([]);
  const [expiryDates, setExpiryDates] = useState([]);
  const [activeStrategies, setActiveStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [selectedLogs, setSelectedLogs] = useState([]);
  const [strategyAccess, setStrategyAccess] = useState(null);
  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(false);

  const strategyOptions = useMemo(() => {
    if (strategyAccess === null) {
      return STRATEGY_OPTIONS.map((option) => ({ ...option, is_locked: true }));
    }

    const byTemplate = new Map();
    (strategyAccess || [])
      .filter((strategy) => strategy.multi_leg_template)
      .forEach((strategy) => {
        const current = byTemplate.get(strategy.multi_leg_template);
        if (!current || (current.is_locked && !strategy.is_locked)) {
          byTemplate.set(strategy.multi_leg_template, strategy);
        }
      });

    const accessOptions = Array.from(byTemplate.values()).map((strategy) => ({
        value: strategy.multi_leg_template,
        label: strategy.multi_leg_template_label || strategy.strategy_name || strategy.multi_leg_template,
        is_locked: Boolean(strategy.is_locked),
        setting: strategy,
      }));
    const accessValues = new Set(accessOptions.map((option) => option.value));
    const fallbackOptions = STRATEGY_OPTIONS
      .filter((option) => !accessValues.has(option.value))
      .map((option) => ({ ...option, is_locked: true }));

    return [...accessOptions, ...fallbackOptions];
  }, [strategyAccess]);

  const selectedStrategyAccess = useMemo(
    () => strategyOptions.find((strategy) => strategy.value === formData.strategy_name),
    [strategyOptions, formData.strategy_name],
  );

  const previewLegs = useMemo(() => {
    const lowerStrike = Number(formData.lower_strike);
    const higherStrike = Number(formData.higher_strike);

    const configuredLegs = selectedStrategyAccess?.setting?.legs || [];
    if (configuredLegs.length) {
      return configuredLegs.map((leg, index) => ({
        leg_name: leg.leg_name || `LEG_${index + 1}`,
        action: leg.action || leg.transaction_type,
        option_type: leg.option_type,
        strike: leg.strike,
        ratio: leg.ratio || 1,
      }));
    }

    if (["BULL_CALL_SPREAD", "BEAR_CALL_SPREAD", "BEAR_PUT_SPREAD"].includes(formData.strategy_name) && lowerStrike > 0 && higherStrike > 0) {
      const spreadLegs = {
        BULL_CALL_SPREAD: [
          { leg_name: "BUY_LOWER_CALL", action: "BUY", option_type: "CE", strike: lowerStrike },
          { leg_name: "SELL_HIGHER_CALL", action: "SELL", option_type: "CE", strike: higherStrike },
        ],
        BEAR_CALL_SPREAD: [
          { leg_name: "SELL_LOWER_CALL", action: "SELL", option_type: "CE", strike: lowerStrike },
          { leg_name: "BUY_HIGHER_CALL", action: "BUY", option_type: "CE", strike: higherStrike },
        ],
        BEAR_PUT_SPREAD: [
          { leg_name: "SELL_LOWER_PUT", action: "SELL", option_type: "PE", strike: lowerStrike },
          { leg_name: "BUY_HIGHER_PUT", action: "BUY", option_type: "PE", strike: higherStrike },
        ],
      };
      return spreadLegs[formData.strategy_name];
    }

    if (formData.strategy_name === "SHORT_STRADDLE" && lowerStrike > 0) {
      return [
        { leg_name: "SELL_CALL", action: "SELL", option_type: "CE", strike: lowerStrike },
        { leg_name: "SELL_PUT", action: "SELL", option_type: "PE", strike: lowerStrike },
      ];
    }

    return [];
  }, [formData, selectedStrategyAccess]);

  const loadActiveStrategies = async () => {
    setListLoading(true);
    try {
      const params = formData.client_id ? { client_id: Number(formData.client_id) } : {};
      const response = await getActiveMultiLegStrategies(params);
      setActiveStrategies(Array.isArray(response) ? response : []);
    } catch (error) {
      Swal.fire("Error", error.message || "Failed to fetch active strategies.", "error");
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    loadActiveStrategies();
  }, []);

  useEffect(() => {
    const loadStrategyAccess = async () => {
      try {
        const params = { include_locked: true };
        if (formData.client_id) {
          params.client = Number(formData.client_id);
        }
        const response = await getClientMultiLegSettings(params);
        const accessList = Array.isArray(response) ? response : [];
        setStrategyAccess(accessList);
        const selectedUnlocked = accessList.some(
          (strategy) => strategy.multi_leg_template === formData.strategy_name && !strategy.is_locked,
        );
        const firstUnlocked = accessList.find((strategy) => strategy.multi_leg_template && !strategy.is_locked);
        if (firstUnlocked && !selectedUnlocked) {
          setFormData((prev) => ({
            ...prev,
            strategy_name: firstUnlocked.multi_leg_template,
            underlying: firstUnlocked.underlying || prev.underlying,
            expiry: formatExpiryForDropdown(firstUnlocked.expiry_date) || prev.expiry,
            entry_time: firstUnlocked.start_time ? firstUnlocked.start_time.slice(0, 5) : prev.entry_time,
            exit_time: firstUnlocked.end_time ? firstUnlocked.end_time.slice(0, 5) : prev.exit_time,
          }));
        }
      } catch (error) {
        console.error("Error loading multi leg strategy access:", error);
        setStrategyAccess([]);
      }
    };

    loadStrategyAccess();
  }, [formData.client_id]);

  useEffect(() => {
    const loadBrokerChoices = async () => {
      try {
        const response = await getSpecificDetails();
        const normalizedBrokerNames = Array.from(
          new Set(
            (Array.isArray(response?.broker_names) ? response.broker_names : [])
              .map((brokerName) => String(brokerName || "").trim())
              .filter(Boolean),
          ),
        );
        setBrokerNames(normalizedBrokerNames);
        if (normalizedBrokerNames.length) {
          setFormData((prev) => ({
            ...prev,
            broker: normalizedBrokerNames.includes(prev.broker) ? prev.broker : normalizedBrokerNames[0],
          }));
        }
      } catch (error) {
        console.error("Error loading multi leg broker options:", error);
        setBrokerNames([]);
      }
    };

    loadBrokerChoices();
  }, []);

  useEffect(() => {
    const loadExpiryChoices = async () => {
      try {
        const response = await getExpiryDate(formData.underlying);
        const availableExpiries = Array.isArray(response?.expiry_dates) ? response.expiry_dates : [];
        setExpiryDates(availableExpiries);
        setFormData((prev) => ({
          ...prev,
          expiry: availableExpiries.includes(prev.expiry) ? prev.expiry : (availableExpiries[0] || "nearest"),
        }));
      } catch (error) {
        console.error("Error loading expiry options:", error);
        setExpiryDates([]);
        setFormData((prev) => ({
          ...prev,
          expiry: "nearest",
        }));
      }
    };

    if (formData.underlying) {
      loadExpiryChoices();
    }
  }, [formData.underlying]);

  const handleChange = ({ target: { name, value, type, checked } }) => {
    if (name === "strategy_name") {
      const nextStrategy = strategyOptions.find((strategy) => strategy.value === value);
      if (nextStrategy?.is_locked) {
        Swal.fire("Locked", "This multi leg strategy is locked. Please contact admin to enable it.", "info");
        return;
      }
      setFormData((prev) => ({
        ...prev,
        strategy_name: value,
        underlying: nextStrategy?.setting?.underlying || prev.underlying,
        expiry: formatExpiryForDropdown(nextStrategy?.setting?.expiry_date) || prev.expiry,
        entry_time: nextStrategy?.setting?.start_time ? nextStrategy.setting.start_time.slice(0, 5) : prev.entry_time,
        exit_time: nextStrategy?.setting?.end_time ? nextStrategy.setting.end_time.slice(0, 5) : prev.exit_time,
      }));
      return;
    }

    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleExecute = async () => {
    if (selectedStrategyAccess?.is_locked) {
      Swal.fire("Locked", "This multi leg strategy is locked. Please contact admin to enable it.", "info");
      return;
    }

    if (!formData.broker) {
      Swal.fire("Validation Error", "Please select a broker before executing the strategy.", "warning");
      return;
    }

    if (["BULL_CALL_SPREAD", "BEAR_CALL_SPREAD", "BEAR_PUT_SPREAD"].includes(formData.strategy_name)) {
      if (!formData.lower_strike || !formData.higher_strike) {
        Swal.fire("Validation Error", "Lower strike and higher strike are required.", "warning");
        return;
      }
    }

    if (formData.strategy_name === "SHORT_STRADDLE" && !formData.lower_strike) {
      Swal.fire("Validation Error", "ATM strike is required.", "warning");
      return;
    }

    if (!["BULL_CALL_SPREAD", "BEAR_CALL_SPREAD", "BEAR_PUT_SPREAD", "SHORT_STRADDLE"].includes(formData.strategy_name) && !previewLegs.length) {
      Swal.fire("Validation Error", "Please configure this strategy's legs from the assigned multi leg settings before executing.", "warning");
      return;
    }

    setLoading(true);
    try {
      const selectedSetting = selectedStrategyAccess?.setting || {};
      const payload = {
        ...formData,
        broker: formData.broker || selectedSetting.broker,
        underlying: formData.underlying || selectedSetting.underlying || selectedSetting.segment?.short_name || selectedSetting.segment?.name,
        expiry: formData.expiry || selectedSetting.expiry_date,
        product_type: formData.product_type || selectedSetting.product_type,
        order_type: formData.order_type || selectedSetting.order_type,
        entry_time: formData.entry_time || selectedSetting.start_time,
        exit_time: formData.exit_time || selectedSetting.end_time,
        legs: previewLegs.length ? previewLegs : undefined,
        client_id: formData.client_id ? Number(formData.client_id) : undefined,
        lower_strike: formData.lower_strike ? Number(formData.lower_strike) : undefined,
        higher_strike: formData.higher_strike ? Number(formData.higher_strike) : undefined,
        quantity_lots: Number(formData.quantity_lots || 1),
        buffer_percentage: Number(formData.buffer_percentage || 0),
        sell_leg_stop_loss_percentage: Number(formData.sell_leg_stop_loss_percentage || 0),
        combined_trailing_start: Number(formData.combined_trailing_start || 0),
        combined_trailing_gap: Number(formData.combined_trailing_gap || 0),
      };
      const response = await executeMultiLegStrategy(payload);
      await Swal.fire("Success", "Multi-leg strategy executed successfully.", "success");
      setSelectedStrategy(response);
      setSelectedLogs([]);
      await loadActiveStrategies();
    } catch (error) {
      Swal.fire("Error", error.message || "Failed to execute strategy.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (strategyId) => {
    try {
      const [detailResponse, logResponse] = await Promise.all([
        getMultiLegStrategyDetail(strategyId),
        getMultiLegStrategyLogs(strategyId),
      ]);
      setSelectedStrategy(detailResponse);
      setSelectedLogs(Array.isArray(logResponse) ? logResponse : []);
    } catch (error) {
      Swal.fire("Error", error.message || "Failed to load strategy details.", "error");
    }
  };

  const handleExit = async (strategyId) => {
    try {
      await exitMultiLegStrategy(strategyId, { reason: "Manual exit from multi-leg console" });
      await Swal.fire("Success", "Strategy exit initiated successfully.", "success");
      await loadActiveStrategies();
      if (selectedStrategy?.id === strategyId) {
        await handleViewDetails(strategyId);
      }
    } catch (error) {
      Swal.fire("Error", error.message || "Failed to exit strategy.", "error");
    }
  };

  const handleKillSwitch = async () => {
    try {
      await killSwitchMultiLegStrategies({
        client_id: formData.client_id ? Number(formData.client_id) : undefined,
        reason: "Kill switch from multi-leg console",
      });
      await Swal.fire("Success", "Kill switch executed successfully.", "success");
      setSelectedStrategy(null);
      setSelectedLogs([]);
      await loadActiveStrategies();
    } catch (error) {
      Swal.fire("Error", error.message || "Failed to run kill switch.", "error");
    }
  };

  return (
    <div className="container-fluid">
      <Row>
        <Col xl={5}>
          <Card>
            <CardBody>
              <div className="d-flex justify-content-between align-items-center mb-4">
                <div>
                  <h4 className="mb-1">Multi Leg Execution</h4>
                  <p className="text-muted mb-0">Bull Call Spread is wired first on the backend foundation.</p>
                </div>
                <Button color="danger" outline onClick={handleKillSwitch}>
                  Kill Switch
                </Button>
              </div>

              <Row className="g-3">
                <Col md={6}>
                  <Label>Client ID</Label>
                  <Input name="client_id" value={formData.client_id} onChange={handleChange} placeholder="Optional for admin" />
                </Col>
                <Col md={6}>
                  <Label>Broker</Label>
                  <Input type="select" name="broker" value={formData.broker} onChange={handleChange}>
                    {brokerNames.length ? (
                      brokerNames.map((brokerName) => (
                        <option key={brokerName} value={brokerName}>
                          {brokerName}
                        </option>
                      ))
                    ) : (
                      <option value="">No broker available</option>
                    )}
                  </Input>
                </Col>
                <Col md={6}>
                  <Label>Strategy</Label>
                  <Input type="select" name="strategy_name" value={formData.strategy_name} onChange={handleChange}>
                    {strategyOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}{option.is_locked ? " (Locked)" : ""}
                      </option>
                    ))}
                  </Input>
                  {selectedStrategyAccess?.is_locked ? (
                    <small className="text-muted">Locked by admin assignment.</small>
                  ) : null}
                </Col>
                <Col md={6}>
                  <Label>Underlying</Label>
                  <Input type="select" name="underlying" value={formData.underlying} onChange={handleChange}>
                    {UNDERLYING_OPTIONS.map((underlying) => (
                      <option key={underlying} value={underlying}>{underlying}</option>
                    ))}
                  </Input>
                </Col>
                <Col md={6}>
                  <Label>Expiry</Label>
                  <Input type="select" name="expiry" value={formData.expiry} onChange={handleChange}>
                    {formData.expiry && !expiryDates.includes(formData.expiry) ? (
                      <option value={formData.expiry}>{formData.expiry}</option>
                    ) : null}
                    {expiryDates.length ? (
                      expiryDates.map((expiryValue) => (
                        <option key={expiryValue} value={expiryValue}>
                          {expiryValue}
                        </option>
                      ))
                    ) : (
                      <option value="nearest">Nearest Expiry</option>
                    )}
                  </Input>
                </Col>
                <Col md={6}>
                  <Label>Lots</Label>
                  <Input type="number" min="1" name="quantity_lots" value={formData.quantity_lots} onChange={handleChange} />
                </Col>
                <Col md={6}>
                  <Label>Lower Strike</Label>
                  <Input type="number" name="lower_strike" value={formData.lower_strike} onChange={handleChange} />
                </Col>
                <Col md={6}>
                  <Label>Higher Strike</Label>
                  <Input type="number" name="higher_strike" value={formData.higher_strike} onChange={handleChange} />
                </Col>
                <Col md={6}>
                  <Label>Order Type</Label>
                  <Input type="select" name="order_type" value={formData.order_type} onChange={handleChange}>
                    <option value="LIMIT">LIMIT</option>
                    <option value="MARKET">MARKET</option>
                    <option value="SL">SL</option>
                    <option value="SL-M">SL-M</option>
                  </Input>
                </Col>
                <Col md={6}>
                  <Label>Buffer %</Label>
                  <Input type="number" step="0.1" name="buffer_percentage" value={formData.buffer_percentage} onChange={handleChange} />
                </Col>
                <Col md={6}>
                  <Label>Sell Leg SL %</Label>
                  <Input type="number" step="0.1" name="sell_leg_stop_loss_percentage" value={formData.sell_leg_stop_loss_percentage} onChange={handleChange} />
                </Col>
                <Col md={6}>
                  <Label>Trailing Start</Label>
                  <Input type="number" name="combined_trailing_start" value={formData.combined_trailing_start} onChange={handleChange} />
                </Col>
                <Col md={6}>
                  <Label>Trailing Gap</Label>
                  <Input type="number" name="combined_trailing_gap" value={formData.combined_trailing_gap} onChange={handleChange} />
                </Col>
                <Col md={6}>
                  <Label>Entry Time</Label>
                  <Input type="time" name="entry_time" value={formData.entry_time} onChange={handleChange} />
                </Col>
                <Col md={6}>
                  <Label>Exit Time</Label>
                  <Input type="time" name="exit_time" value={formData.exit_time} onChange={handleChange} />
                </Col>
                <Col md={12}>
                  <div className="form-check">
                    <Input className="form-check-input" type="checkbox" name="allow_reentry" checked={formData.allow_reentry} onChange={handleChange} />
                    <Label className="form-check-label">Allow re-entry</Label>
                  </div>
                </Col>
              </Row>

              <div className="d-flex gap-2 mt-4">
                <Button color="primary" onClick={handleExecute} disabled={loading}>
                  {loading ? "Executing..." : "Execute Strategy"}
                </Button>
                <Button color="light" onClick={loadActiveStrategies} disabled={listLoading}>
                  Refresh Active
                </Button>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <h5 className="mb-3">Preview Legs</h5>
              <Table responsive>
                <thead>
                  <tr>
                    <th>Leg</th>
                    <th>Action</th>
                    <th>Type</th>
                    <th>Strike</th>
                  </tr>
                </thead>
                <tbody>
                  {previewLegs.length ? (
                    previewLegs.map((leg) => (
                      <tr key={leg.leg_name}>
                        <td>{leg.leg_name}</td>
                        <td>{leg.action}</td>
                        <td>{leg.option_type}</td>
                        <td>{leg.strike}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="text-muted">
                        Strategy preview will appear here for the selected setup.
                      </td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </CardBody>
          </Card>
        </Col>

        <Col xl={7}>
          <Card>
            <CardBody>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="mb-0">Active Strategies</h5>
                <Badge color="light" pill>
                  {activeStrategies.length} active
                </Badge>
              </div>
              <Table responsive>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Strategy</th>
                    <th>Underlying</th>
                    <th>Status</th>
                    <th>Combined P&L</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {activeStrategies.length ? (
                    activeStrategies.map((strategy) => (
                      <tr key={strategy.id}>
                        <td>{strategy.id}</td>
                        <td>{strategy.strategy_name}</td>
                        <td>{strategy.underlying}</td>
                        <td>
                          <Badge color={statusColor(strategy.status)}>{strategy.status}</Badge>
                        </td>
                        <td>{strategy.combined_pnl}</td>
                        <td className="d-flex gap-2">
                          <Button size="sm" color="info" outline onClick={() => handleViewDetails(strategy.id)}>
                            View
                          </Button>
                          <Button size="sm" color="danger" outline onClick={() => handleExit(strategy.id)}>
                            Exit
                          </Button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" className="text-muted">
                        {listLoading ? "Loading active strategies..." : "No active multi-leg strategies found."}
                      </td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="mb-0">Strategy Detail</h5>
                {selectedStrategy?.status ? (
                  <Badge color={statusColor(selectedStrategy.status)}>{selectedStrategy.status}</Badge>
                ) : null}
              </div>

              {selectedStrategy ? (
                <>
                  <Row className="mb-3">
                    <Col md={4}><strong>ID:</strong> {selectedStrategy.id}</Col>
                    <Col md={4}><strong>Strategy:</strong> {selectedStrategy.strategy_name}</Col>
                    <Col md={4}><strong>Exit Reason:</strong> {selectedStrategy.exit_reason || "-"}</Col>
                  </Row>
                  <Row className="mb-3">
                    <Col md={4}><strong>Underlying:</strong> {selectedStrategy.underlying}</Col>
                    <Col md={4}><strong>Total Qty:</strong> {selectedStrategy.total_quantity}</Col>
                    <Col md={4}><strong>Combined P&L:</strong> {selectedStrategy.combined_pnl}</Col>
                  </Row>
                  <Table responsive>
                    <thead>
                      <tr>
                        <th>Leg</th>
                        <th>Action</th>
                        <th>Symbol</th>
                        <th>Qty</th>
                        <th>Status</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>P&L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(selectedStrategy.legs || []).map((leg) => (
                        <tr key={leg.id}>
                          <td>{leg.leg_name}</td>
                          <td>{leg.transaction_type}</td>
                          <td>{leg.symbol}</td>
                          <td>{leg.quantity}</td>
                          <td>{leg.status}</td>
                          <td>{leg.entry_price ?? "-"}</td>
                          <td>{leg.exit_price ?? "-"}</td>
                          <td>{leg.pnl}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>

                  <h6 className="mt-4">Execution Logs</h6>
                  <Table responsive>
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Event</th>
                        <th>Message</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedLogs.length ? (
                        selectedLogs.map((log) => (
                          <tr key={log.id}>
                            <td>{new Date(log.created_at).toLocaleString()}</td>
                            <td>{log.event_type}</td>
                            <td>{log.message}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="3" className="text-muted">No logs available for this execution.</td>
                        </tr>
                      )}
                    </tbody>
                  </Table>
                </>
              ) : (
                <p className="text-muted mb-0">Select an active strategy to inspect its legs, P&amp;L, and audit logs.</p>
              )}
            </CardBody>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default MultiLegExecutionPage;
