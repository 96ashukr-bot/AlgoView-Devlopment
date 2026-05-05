import React, { useEffect, useMemo, useState } from "react";
import { Button, Card, CardBody, Col, Input, Label, Row, Table } from "reactstrap";
import { useNavigate, useParams } from "react-router-dom";
import Swal from "sweetalert2";
import {
  clearClientMultiLegSetting,
  executeMultiLegStrategy,
  getActiveMultiLegStrategies,
  getClientMultiLegSettings,
  getExpiryDate,
  getSpecificDetails,
  killSwitchMultiLegStrategies,
  updateClientMultiLegSetting,
} from "../../../Services/Authentication";

const DEFAULT_BUFFER_PERCENTAGE = 2.5;
const MIN_BUFFER_PERCENTAGE = 0.1;
const MAX_BUFFER_PERCENTAGE = 10;

const UNDERLYING_OPTIONS = ["NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY"];
const EXPIRY_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

const formatExpiryForDropdown = (value) => {
  const rawValue = String(value || "").trim().toUpperCase();
  if (!rawValue) {
    return "";
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

const hasSavedLegs = (setting) => Array.isArray(setting?.legs) && setting.legs.length > 0;

const TEMPLATE_DEFAULTS = {
  SHORT_STRADDLE: [
    { option_type: "CE", action: "SELL", ratio: 1 },
    { option_type: "PE", action: "SELL", ratio: 1 },
  ],
  BULL_CALL_SPREAD: [
    { option_type: "CE", action: "BUY", ratio: 1 },
    { option_type: "CE", action: "SELL", ratio: 1 },
  ],
  BEAR_PUT_SPREAD: [
    { option_type: "PE", action: "BUY", ratio: 1 },
    { option_type: "PE", action: "SELL", ratio: 1 },
  ],
  LONG_CALL_BUTTERFLY: [
    { option_type: "CE", action: "BUY", ratio: 1 },
    { option_type: "CE", action: "SELL", ratio: 2 },
    { option_type: "CE", action: "BUY", ratio: 1 },
  ],
  SHORT_CALL_BUTTERFLY: [
    { option_type: "CE", action: "SELL", ratio: 1 },
    { option_type: "CE", action: "BUY", ratio: 2 },
    { option_type: "CE", action: "SELL", ratio: 1 },
  ],
  LONG_CALL_CONDOR: [
    { option_type: "CE", action: "BUY", ratio: 1 },
    { option_type: "CE", action: "SELL", ratio: 1 },
    { option_type: "CE", action: "SELL", ratio: 1 },
    { option_type: "CE", action: "BUY", ratio: 1 },
  ],
  SHORT_CALL_CONDOR: [
    { option_type: "CE", action: "SELL", ratio: 1 },
    { option_type: "CE", action: "BUY", ratio: 1 },
    { option_type: "CE", action: "BUY", ratio: 1 },
    { option_type: "CE", action: "SELL", ratio: 1 },
  ],
  LONG_IRON_CONDOR: [
    { option_type: "PE", action: "BUY", ratio: 1 },
    { option_type: "PE", action: "SELL", ratio: 1 },
    { option_type: "CE", action: "SELL", ratio: 1 },
    { option_type: "CE", action: "BUY", ratio: 1 },
  ],
  SHORT_IRON_BUTTERFLY: [
    { option_type: "PE", action: "BUY", ratio: 1 },
    { option_type: "PE", action: "SELL", ratio: 1 },
    { option_type: "CE", action: "SELL", ratio: 1 },
    { option_type: "CE", action: "BUY", ratio: 1 },
  ],
};

const MultiLegEditPage = () => {
  const { strategyId } = useParams();
  const navigate = useNavigate();
  const [setting, setSetting] = useState(null);
  const [brokerNames, setBrokerNames] = useState([]);
  const [expiryDates, setExpiryDates] = useState([]);
  const [activeStrategies, setActiveStrategies] = useState([]);
  const [saving, setSaving] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [killSwitchLoading, setKillSwitchLoading] = useState(false);
  const [formData, setFormData] = useState({
    productType: "",
    underlying: "NIFTY",
    orderType: "LIMIT",
    bufferPercentage: String(DEFAULT_BUFFER_PERCENTAGE),
    quantity: "",
    stopLoss: "",
    slType: "",
    target: "",
    tradeLimit: "",
    maxLoss: "",
    maxProfit: "",
    expiry: "",
    startTime: "09:30",
    endTime: "15:15",
    legs: [],
  });

  const applySettingToForm = async (currentSetting) => {
    setSetting(currentSetting);

    if (!currentSetting) {
      return;
    }

    setFormData({
      productType: currentSetting.product_type || "",
      underlying:
        currentSetting.underlying
        || currentSetting.segment?.short_name
        || currentSetting.segment?.name
        || "NIFTY",
      orderType: currentSetting.order_type || "LIMIT",
      bufferPercentage:
        currentSetting.buffer_percentage !== null && currentSetting.buffer_percentage !== undefined
          ? String(currentSetting.buffer_percentage)
          : String(DEFAULT_BUFFER_PERCENTAGE),
      quantity: currentSetting.quantity || "",
      stopLoss: currentSetting.stop_loss || "",
      slType: currentSetting.sl_type || "",
      target: currentSetting.target || "",
      tradeLimit: currentSetting.trade_limit || "",
      maxLoss: currentSetting.max_loss_for_day || "",
      maxProfit: currentSetting.max_profit_for_day || "",
      expiry: formatExpiryForDropdown(currentSetting.expiry_date),
      startTime: currentSetting.start_time ? currentSetting.start_time.slice(0, 5) : "09:30",
      endTime: currentSetting.end_time ? currentSetting.end_time.slice(0, 5) : "15:15",
      legs: currentSetting.legs?.length
        ? currentSetting.legs
        : (TEMPLATE_DEFAULTS[currentSetting.multi_leg_template] || []).map((leg) => ({ ...leg, strike: "" })),
    });

    const selectedUnderlying =
      currentSetting.underlying
      || currentSetting?.segment?.short_name
      || currentSetting?.segment?.name
      || "NIFTY";
    const expiryResponse = await getExpiryDate(selectedUnderlying);
    setExpiryDates(Array.isArray(expiryResponse?.expiry_dates) ? expiryResponse.expiry_dates : []);
  };

  const loadActiveStrategies = async () => {
    try {
      const response = await getActiveMultiLegStrategies();
      setActiveStrategies(Array.isArray(response) ? response : []);
    } catch (error) {
      console.error("Error loading active multi leg strategies:", error);
      setActiveStrategies([]);
    }
  };

  const fetchPageData = async () => {
      try {
        const [multiLegData, clientDetails] = await Promise.all([
          getClientMultiLegSettings({ strategy: strategyId }),
          getSpecificDetails(),
        ]);

        const currentSetting = Array.isArray(multiLegData) ? multiLegData[0] : null;
        setBrokerNames(clientDetails?.broker_names || []);
        await applySettingToForm(currentSetting);
        await loadActiveStrategies();
      } catch (error) {
        console.error("Error loading multi leg setting:", error);
      }
  };

  useEffect(() => {
    fetchPageData();
  }, [strategyId]);

  const strategyLabel = useMemo(() => {
    if (!setting) {
      return "Multi Leg Strategy";
    }
    return `${setting.strategy_name} (${setting.multi_leg_template_label || "Multi Leg"})`;
  }, [setting]);

  const runningExecutionsForStrategy = useMemo(() => {
    if (!setting) {
      return [];
    }
    return activeStrategies.filter((strategy) => strategy.strategy_name === setting.multi_leg_template);
  }, [activeStrategies, setting]);

  useEffect(() => {
    const loadExpiryChoices = async () => {
      try {
        const expiryResponse = await getExpiryDate(formData.underlying);
        const availableExpiries = Array.isArray(expiryResponse?.expiry_dates) ? expiryResponse.expiry_dates : [];
        setExpiryDates(availableExpiries);
        setFormData((prev) => ({
          ...prev,
          expiry: availableExpiries.includes(prev.expiry) ? prev.expiry : (availableExpiries[0] || prev.expiry),
        }));
      } catch (error) {
        console.error("Error loading index expiries:", error);
        setExpiryDates([]);
      }
    };

    if (formData.underlying) {
      loadExpiryChoices();
    }
  }, [formData.underlying]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => {
      const next = {
        ...prev,
        [name]: name === "orderType" ? value.toUpperCase() : value,
      };
      if (name === "orderType" && value.toUpperCase() === "MARKET") {
        next.bufferPercentage = "";
      }
      if (name === "orderType" && value.toUpperCase() === "LIMIT" && !next.bufferPercentage) {
        next.bufferPercentage = String(DEFAULT_BUFFER_PERCENTAGE);
      }
      return next;
    });
  };

  const handleLegChange = (index, field, value) => {
    setFormData((prev) => ({
      ...prev,
      legs: prev.legs.map((leg, legIndex) => (
        legIndex === index ? { ...leg, [field]: value } : leg
      )),
    }));
  };

  const handleCancel = () => {
    navigate("/dashboard/algoviewtech/user");
  };

  const handleKillSwitch = async () => {
    if (!setting) {
      return;
    }

    const hasRunningTrade = runningExecutionsForStrategy.length > 0;
    const result = await Swal.fire({
      title: hasRunningTrade ? "Exit running trades?" : "Delete saved legs?",
      text: hasRunningTrade
        ? "This will square off all running multi-leg trades for this client."
        : "No running trade was found. This will delete the saved leg configuration for this strategy.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: hasRunningTrade ? "Yes, exit trades" : "Yes, delete saved legs",
      cancelButtonText: "Cancel",
    });

    if (!result.isConfirmed) {
      return;
    }

    setKillSwitchLoading(true);
    try {
      if (hasRunningTrade) {
        const response = await killSwitchMultiLegStrategies({
          reason: `Kill switch from saved leg page for ${setting.strategy_name}`,
        });
        await loadActiveStrategies();
        Swal.fire(
          "Kill Switch Complete",
          `${response?.exited_strategy_ids?.length || 0} running multi-leg trade(s) were sent for exit.`,
          "success",
        );
      } else {
        const clearedSetting = await clearClientMultiLegSetting(setting.strategy);
        await applySettingToForm(clearedSetting);
        Swal.fire("Deleted", "Saved leg configuration has been cleared.", "success");
      }
    } catch (error) {
      Swal.fire("Error!", error.message || "Kill switch action failed.", "error");
    } finally {
      setKillSwitchLoading(false);
    }
  };

  const handleSave = async () => {
    const result = await Swal.fire({
      text: "Do you want to save the changes?",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Yes, save it!",
      cancelButtonText: "No, cancel!",
    });

    if (!result.isConfirmed || !setting) {
      return;
    }

    if (!formData.expiry) {
      Swal.fire("Validation Error", "Expiry is required.", "warning");
      return;
    }

    if (!formData.startTime || !formData.endTime) {
      Swal.fire("Validation Error", "Start time and end time are required.", "warning");
      return;
    }

    if (formData.startTime >= formData.endTime) {
      Swal.fire("Validation Error", "End time must be after start time.", "warning");
      return;
    }

    const invalidLeg = formData.legs.find((leg) => !leg.strike || Number(leg.strike) <= 0);
    if (invalidLeg) {
      Swal.fire("Validation Error", "Each leg strike must be greater than 0.", "warning");
      return;
    }

    if (formData.orderType === "LIMIT") {
      const bufferValue = parseFloat(formData.bufferPercentage);
      if (Number.isNaN(bufferValue) || bufferValue < MIN_BUFFER_PERCENTAGE || bufferValue > MAX_BUFFER_PERCENTAGE) {
        Swal.fire(
          "Validation Error",
          `Buffer percentage must be between ${MIN_BUFFER_PERCENTAGE} and ${MAX_BUFFER_PERCENTAGE}.`,
          "warning",
        );
        return;
      }
    }

    const payload = {
      strategy: setting.strategy,
      segment: setting.segment?.id || null,
      underlying: formData.underlying,
      group_service: setting.group_service,
      broker: setting.broker,
      product_type: formData.productType,
      order_type: formData.orderType,
      buffer_percentage: formData.orderType === "LIMIT" ? parseFloat(formData.bufferPercentage) : null,
      quantity: formData.quantity || null,
      stop_loss: formData.stopLoss || null,
      sl_type: formData.slType || null,
      target: formData.target || null,
      trade_limit: formData.tradeLimit || null,
      max_loss_for_day: formData.maxLoss || null,
      max_profit_for_day: formData.maxProfit || null,
      expiry_date: formData.expiry || null,
      start_time: formData.startTime,
      end_time: formData.endTime,
      legs: formData.legs.map((leg) => ({
        option_type: leg.option_type,
        action: leg.action,
        ratio: Number(leg.ratio) || 1,
        strike: Number(leg.strike),
      })),
    };

    setSaving(true);
    try {
      const savedSetting = await updateClientMultiLegSetting(payload);
      await applySettingToForm(savedSetting);
      Swal.fire("Saved!", "Your multi leg strategy has been saved.", "success");
    } catch (error) {
      Swal.fire("Error!", error.message || "There was an error saving your changes.", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleExecute = async () => {
    if (!setting) {
      return;
    }

    if (!formData.expiry) {
      Swal.fire("Validation Error", "Expiry is required.", "warning");
      return;
    }

    if (!formData.quantity || Number(formData.quantity) <= 0) {
      Swal.fire("Validation Error", "Quantity must be greater than 0.", "warning");
      return;
    }

    if (!formData.startTime || !formData.endTime) {
      Swal.fire("Validation Error", "Start time and end time are required.", "warning");
      return;
    }

    if (formData.startTime >= formData.endTime) {
      Swal.fire("Validation Error", "End time must be after start time.", "warning");
      return;
    }

    const invalidLeg = formData.legs.find((leg) => !leg.strike || Number(leg.strike) <= 0);
    if (invalidLeg) {
      Swal.fire("Validation Error", "Each leg strike must be greater than 0.", "warning");
      return;
    }

    if (formData.orderType === "LIMIT") {
      const bufferValue = parseFloat(formData.bufferPercentage);
      if (Number.isNaN(bufferValue) || bufferValue < MIN_BUFFER_PERCENTAGE || bufferValue > MAX_BUFFER_PERCENTAGE) {
        Swal.fire(
          "Validation Error",
          `Buffer percentage must be between ${MIN_BUFFER_PERCENTAGE} and ${MAX_BUFFER_PERCENTAGE}.`,
          "warning",
        );
        return;
      }
    }

    const legs = formData.legs.map((leg, index) => ({
      leg_name: leg.leg_name || `LEG_${index + 1}`,
      option_type: leg.option_type,
      transaction_type: leg.action,
      action: leg.action,
      ratio: Number(leg.ratio) || 1,
      strike: Number(leg.strike),
    }));
    const strikes = legs.map((leg) => Number(leg.strike)).filter((strike) => strike > 0).sort((a, b) => a - b);

    const payload = {
      strategy_name: setting.multi_leg_template,
      broker: setting.broker,
      underlying: formData.underlying,
      expiry: formData.expiry,
      group_service: setting.group_service || "",
      product_type: formData.productType || setting.product_type || "INTRADAY",
      order_type: formData.orderType,
      buffer_percentage: formData.orderType === "LIMIT" ? parseFloat(formData.bufferPercentage) : undefined,
      quantity_lots: Number(formData.quantity),
      sell_leg_stop_loss_percentage: formData.stopLoss ? Number(formData.stopLoss) : undefined,
      combined_trailing_start: formData.maxProfit ? Number(formData.maxProfit) : undefined,
      combined_trailing_gap: formData.target ? Number(formData.target) : undefined,
      entry_time: formData.startTime,
      exit_time: formData.endTime,
      legs,
      lower_strike: strikes[0],
      higher_strike: strikes[strikes.length - 1],
    };

    setExecuting(true);
    try {
      await executeMultiLegStrategy(payload);
      await loadActiveStrategies();
      Swal.fire("Executed", "Multi-leg strategy order execution has been initiated.", "success");
    } catch (error) {
      Swal.fire("Error!", error.message || "There was an error executing the strategy.", "error");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div style={{ paddingTop: "20px" }}>
      <Card>
        <CardBody>
          <div className="container mt-5" style={{ paddingTop: "25px" }}>
            <div className="mb-4" style={{ position: "absolute", top: "20px", left: "20px" }}>
              <h5 style={{ margin: 0, fontWeight: "bold", color: "black" }}>{strategyLabel}</h5>
            </div>

            <Row className="mb-4">
              <Col md={2}>
                <Label>Index</Label>
                <Input type="select" name="underlying" value={formData.underlying} onChange={handleChange}>
                  {UNDERLYING_OPTIONS.map((underlying) => (
                    <option key={underlying} value={underlying}>{underlying}</option>
                  ))}
                </Input>
              </Col>
              <Col md={2}>
                <Label>Expiry</Label>
                <Input type="select" name="expiry" value={formData.expiry} onChange={handleChange}>
                  {expiryDates.length ? (
                    expiryDates.map((expiry) => (
                      <option key={expiry} value={expiry}>{expiry}</option>
                    ))
                  ) : (
                    <option value={formData.expiry || ""}>{formData.expiry || "No expiry available"}</option>
                  )}
                </Input>
              </Col>
              <Col md={2}>
                <Label>Group Service</Label>
                <Input value={setting?.group_service || ""} readOnly />
              </Col>
              <Col md={2}>
                <Label>Broker</Label>
                <Input type="select" name="broker" value={setting?.broker || ""} readOnly>
                  <option value={setting?.broker || ""}>{setting?.broker || "No Broker"}</option>
                  {brokerNames.map((name) => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </Input>
              </Col>
              <Col md={2}>
                <Label>Product Type</Label>
                <Input type="select" name="productType" value={formData.productType} onChange={handleChange}>
                  <option value="">Select Product Type</option>
                  <option value="MIS">MIS</option>
                  <option value="CNC">CNC</option>
                  <option value="NRML">NRML</option>
                </Input>
              </Col>
              <Col md={2}>
                <Label>Order Type</Label>
                <Input type="select" name="orderType" value={formData.orderType} onChange={handleChange}>
                  <option value="MARKET">MARKET</option>
                  <option value="LIMIT">LIMIT</option>
                </Input>
              </Col>
              {formData.orderType === "LIMIT" && (
                <Col md={2} className="mt-3">
                  <Label>Buffer %</Label>
                  <Input
                    type="number"
                    name="bufferPercentage"
                    min={MIN_BUFFER_PERCENTAGE}
                    max={MAX_BUFFER_PERCENTAGE}
                    step="0.1"
                    value={formData.bufferPercentage}
                    onChange={handleChange}
                  />
                </Col>
              )}
            </Row>

            <div className="table-responsive-sm" style={{ overflowX: "auto" }}>
              <Table bordered>
                <thead>
                  <tr>
                    <th>Leg</th>
                    <th>Action</th>
                    <th>Option Type</th>
                    <th>Strike</th>
                    <th>Ratio</th>
                  </tr>
                </thead>
                <tbody>
                  {formData.legs.map((leg, index) => (
                    <tr key={`${leg.option_type}-${leg.action}-${index}`}>
                      <td>Leg {index + 1}</td>
                      <td>{leg.action}</td>
                      <td>{leg.option_type}</td>
                      <td>
                        <Input
                          type="number"
                          min="1"
                          value={leg.strike || ""}
                          onChange={(event) => handleLegChange(index, "strike", event.target.value)}
                        />
                      </td>
                      <td>
                        <Input
                          type="number"
                          min="1"
                          value={leg.ratio || 1}
                          onChange={(event) => handleLegChange(index, "ratio", event.target.value)}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>

            <Row className="mt-3">
              <Col md={2}>
                <Label>Quantity</Label>
                <Input type="number" name="quantity" min="1" value={formData.quantity} onChange={handleChange} />
              </Col>
              <Col md={2}>
                <Label>Stop-Loss</Label>
                <Input type="number" name="stopLoss" min="1" value={formData.stopLoss} onChange={handleChange} />
              </Col>
              <Col md={2}>
                <Label>SL-TP Type</Label>
                <Input type="select" name="slType" value={formData.slType} onChange={handleChange}>
                  <option value="">--</option>
                  <option value="POINTS">Points</option>
                  <option value="PERCENTAGE">%</option>
                </Input>
              </Col>
              <Col md={2}>
                <Label>Target</Label>
                <Input type="number" name="target" min="1" value={formData.target} onChange={handleChange} />
              </Col>
              <Col md={2}>
                <Label>Trade Limit</Label>
                <Input type="number" name="tradeLimit" min="1" value={formData.tradeLimit} onChange={handleChange} />
              </Col>
              <Col md={2}>
                <Label>Max Loss For Day</Label>
                <Input type="number" name="maxLoss" value={formData.maxLoss} onChange={handleChange} />
              </Col>
              <Col md={2} className="mt-3">
                <Label>Max Profit For Day</Label>
                <Input type="number" name="maxProfit" value={formData.maxProfit} onChange={handleChange} />
              </Col>
              <Col md={2} className="mt-3">
                <Label>Start Time</Label>
                <Input type="time" name="startTime" value={formData.startTime} onChange={handleChange} />
              </Col>
              <Col md={2} className="mt-3">
                <Label>End Time</Label>
                <Input type="time" name="endTime" value={formData.endTime} onChange={handleChange} />
              </Col>
            </Row>

            <div className="d-flex justify-content-end mt-4">
              <Button color="danger" className="me-3" onClick={handleCancel}>
                Cancel
              </Button>
              <Button color="warning" className="me-3" onClick={handleKillSwitch} disabled={!setting || killSwitchLoading}>
                {killSwitchLoading ? "Processing..." : "Kill Switch"}
              </Button>
              <Button className="btn btn-primary search-btn-clr" onClick={handleExecute} disabled={!setting || executing}>
                {executing ? "Executing..." : "Execute"}
              </Button>
            </div>

            <div className="mt-4">
              <h6 className="mb-3" style={{ fontWeight: 700 }}>Saved Legs</h6>
              {hasSavedLegs(setting) ? (
                <div className="table-responsive-sm" style={{ overflowX: "auto" }}>
                  <Table bordered>
                    <thead>
                      <tr>
                        <th>Leg</th>
                        <th>Action</th>
                        <th>Option Type</th>
                        <th>Strike</th>
                        <th>Ratio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {setting.legs.map((leg, index) => (
                        <tr key={`saved-${leg.option_type}-${leg.action}-${index}`}>
                          <td>Leg {index + 1}</td>
                          <td>{leg.action}</td>
                          <td>{leg.option_type}</td>
                          <td>{leg.strike}</td>
                          <td>{leg.ratio || 1}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                  <Row className="mt-2">
                    <Col md={3}><strong>Index:</strong> {setting.underlying || "--"}</Col>
                    <Col md={3}><strong>Expiry:</strong> {formatExpiryForDropdown(setting.expiry_date) || "--"}</Col>
                    <Col md={3}><strong>Start:</strong> {setting.start_time ? setting.start_time.slice(0, 5) : "--"}</Col>
                    <Col md={3}><strong>End:</strong> {setting.end_time ? setting.end_time.slice(0, 5) : "--"}</Col>
                  </Row>
                  <div className="mt-2">
                    {runningExecutionsForStrategy.length > 0 ? (
                      <small className="text-success">{runningExecutionsForStrategy.length} running trade(s) found for this strategy.</small>
                    ) : (
                      <small className="text-muted">No running trade found. Kill Switch will delete this saved leg configuration.</small>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-muted">No saved legs found for this strategy.</div>
              )}
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default MultiLegEditPage;
