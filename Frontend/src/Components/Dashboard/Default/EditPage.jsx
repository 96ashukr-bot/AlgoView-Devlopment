import React, { useState, useEffect } from "react";
import { Button, Input, Col, Row, Table, CardBody, Card, Label } from "reactstrap";
import { useNavigate, useParams } from "react-router-dom";
import { getClientTradeSetting, getSpecificDetails, updateTradeClient, getExpiryDate, } from "../../../Services/Authentication";
import Swal from 'sweetalert2';

const EditPage = () => {
  const { clientId, segmentId, subSegmentId } = useParams();
  // console.log('ididididdidi', clientId, segmentId, subSegmentId);
  const [formData, setFormData] = useState({
    symbol: "",
    expiry: "",
    groupService: "",
    broker: "",
    productType: "",
    quantity: "",
    stopLoss: "",
    slType: "",
    target: "",
    tradeLimit: "",
    maxLoss: "",
    minLoss: "",
    maxProfit: "",
    minProfit: "",
  });

  const [apiData, setApiData] = useState([]);
  const [serviceNameToQty, setServiceNameToQty] = useState({});
  const [expiryDates, setExpiryDates] = useState([]);
  const navigate = useNavigate();
  // const [broker, setBroker] = useState([]);
  const [groupService, setGroupService] = useState([]);
  const [symbols, setSymbols] = useState([]);
  const [brokerNames, setBrokerNames] = useState([]);

  useEffect(() => {
    if (clientId && segmentId && subSegmentId) {
      fetchData(clientId, segmentId, subSegmentId);
      fetchSpecificDetails(clientId);

    }
  }, [clientId, segmentId, subSegmentId]);


  const fetchExpiryDates = async (short_name) => {
    if (!short_name) {
      console.error("Short Name is required to fetch expiry dates.");
      return;
    }

    try {
      const response = await getExpiryDate(short_name);
      if (response && Array.isArray(response.expiry_dates)) {
        setExpiryDates(response.expiry_dates);

        setFormData((prev) => ({
          ...prev,
          expiry: response.expiry_dates.includes(prev.expiry) ? prev.expiry : response.expiry_dates[0],
        }));
      } else {
        console.error("Invalid expiry dates format.");
      }
    } catch (error) {
      console.error("Error fetching expiry dates:", error);
    }
  };

  const fetchSpecificDetails = async (clientId) => {
    try {
      const response = await getSpecificDetails(clientId);
      if (response) {
        // If broker_names array is available, set it
        if (response.broker_names) {
          setBrokerNames(response.broker_names);
        } else {
          console.error("Broker names data is not available.");
          setBrokerNames([]);
        }

        if (response?.Group_service?.json_data) {
          const qtyMap = response.Group_service.json_data.reduce((map, item) => {
            map[item.ServiceName] = parseInt(item.Qty, 10);
            return map;
          }, {});
          setServiceNameToQty(qtyMap);
        }

        if (response.Group_service) {
          const groupServiceName = response.Group_service.group_name;
          setGroupService([{ name: groupServiceName }]);
        }
      }
    } catch (error) {
      console.error("Failed to load specific details:", error);
    }
  };

  const fetchData = async (clientId, segmentId, subSegmentId) => {
    try {
      const data = await getClientTradeSetting(clientId, segmentId, subSegmentId);
      setApiData(data);
      // console.log('dataaaaaaaaa',data);

      // Extract unique group services from the API response
      const uniqueGroupServices = Array.from(new Set(data.map(item => item.group_service)));
      setGroupService(uniqueGroupServices.map(service => ({ name: service })));

      fetchExpiryDates(data[0].sub_segment?.short_name);
      if (data && data.length > 0) {
        const symbolList = Array.from(
          new Set(data.map(item => item.sub_segment?.short_name).filter(Boolean))
        );
        setSymbols(symbolList);
        // console.log('datadatadatadata',data);
        const firstItem = data[0];

        console.log('firstItemfirstItemfirstItem', firstItem);

        // Set formData with the latest expiry date
        setFormData({
          symbol: firstItem.sub_segment?.short_name || "",
          expiry: firstItem.expiry_date ? formatExpiryDate(firstItem.expiry_date) : "",
          groupService: firstItem.group_service,
          broker: firstItem.broker,
          productType: firstItem.product_type,
          quantity: firstItem.quantity,
          stopLoss: firstItem.stop_loss,
          slType: firstItem.sl_type,
          target: firstItem.target,
          tradeLimit: firstItem.trade_limit,
          maxLoss: firstItem.max_loss_for_day,
          minLoss: firstItem.min_loss_for_day,
          maxProfit: firstItem.max_profit_for_day,
          minProfit: firstItem.min_profit_for_day,
        });

        const uniqueGroupServices = Array.from(new Set(data.map(item => item.group_service)));
        setGroupService(uniqueGroupServices.map(service => ({ name: service })));

      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  const handleInputChange = (e, index, field) => {
    const { value, name } = e.target;
    const updatedData = [...apiData];

    const serviceName = updatedData[index]?.sub_segment?.name;
    const maxQty = serviceNameToQty[serviceName] || Infinity;

    if (field === "quantity" && value > maxQty) {
      // alert(`Quantity for ${serviceName} cannot exceed ${maxQty}`);
      Swal.fire({
        icon: "warning",
        title: "Quantity Exceeded",
        text: `Quantity for ${serviceName} cannot exceed ${maxQty}`,
        confirmButtonText: "OK",
      });
      return;
    }

    updatedData[index][field] = value;
    setApiData(updatedData);

    setFormData((prev) => {
      const updatedFormData = { ...prev, [name]: value };
      // console.log("Updated formData: cccccc", updatedFormData);
      return updatedFormData;
    });
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const updatedFormData = { ...prev, [name]: value };
      console.log("Updated formData:", updatedFormData);
      return updatedFormData;
    });

    // If symbol is changed, fetch expiry dates only if value is not empty
    if (name === "symbol" && value) {

      fetchExpiryDates(value);
    }
  };

  const handleCancel = () => {
    navigate("/dashboard/algoviewtech/user");
    console.log("Cancelled");
  };

  const formatExpiryDate = (expiry) => {
    const monthMap = {
      "JAN": "01",
      "FEB": "02",
      "MAR": "03",
      "APR": "04",
      "MAY": "05",
      "JUN": "06",
      "JUL": "07",
      "AUG": "08",
      "SEP": "09",
      "OCT": "10",
      "NOV": "11",
      "DEC": "12",
    };

    const monthFormat = {
      "01": "Jan",
      "02": "Feb",
      "03": "Mar",
      "04": "Apr",
      "05": "May",
      "06": "Jun",
      "07": "Jul",
      "08": "Aug",
      "09": "Sep",
      "10": "Oct",
      "11": "Nov",
      "12": "Dec",
    };

    if (expiry.match(/^\d{4}-\d{2}-\d{2}$/)) {
      const [year, month, day] = expiry.split("-");
      const monthAbbr = Object.keys(monthMap).find(key => monthMap[key] === month);
      return `${day}${monthAbbr}${year}`;
    }

    // Assuming expiry is in the format "25Mar2025"
    const day = expiry.slice(0, 2);
    const month = monthMap[expiry.slice(2, 5).toUpperCase()];
    const formatMonths = monthFormat[expiry.slice(2, 5).toUpperCase()];
    const year = `${expiry.slice(5, 9)}`;

    if (!month && !formatMonths) {
      console.error(`Invalid month for expiry: ${expiry}`);
      return null;
    }

    const formattedDate = `${year}-${month}-${day}`;
    console.log('Formatted Expiry Date:', formattedDate);
    return formattedDate;
  };

  const handleOk = async () => {
    const result = await Swal.fire({
      // title: 'Are you sure?',
      text: 'Do you want to save the changes?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText: 'Yes, save it!',
      cancelButtonText: 'No, cancel!',
    });

    if (result.isConfirmed) {

      const payload = {
        segment: parseInt(segmentId, 10),
        sub_segment: parseInt(subSegmentId, 10),
        symbol: formData.symbol,
        group_service: formData.groupService,
        broker: formData.broker,
        product_type: formData.productType,
        sl_type: (formData.slType),
        buy_sell: apiData[0]?.buy_sell || "Buy",
        quantity: formData.quantity || 0,
        stop_loss: formData.stopLoss || 0,
        target: formData.target || 0,
        trade_limit: formData.tradeLimit || 0,
        max_loss_for_day: formData.maxLoss || 0,
        min_loss_for_day: formData.minLoss || 0,
        max_profit_for_day: formData.maxProfit || 0,
        min_profit_for_day: formData.minProfit || 0,
        expiry_date: formatExpiryDate(formData.expiry),
        is_trade_status: true,
      };

      console.log('payload for api call', payload);
      // return;
      try {
        const response = await updateTradeClient(clientId, payload);
        console.log("API Response:", response);
        // fetchData(clientId, segmentId, subSegmentId);
        Swal.fire(
          'Saved!',
          'Your changes have been saved.',
          'success'
        );
        navigate("/dashboard/algoviewtech/user");
      } catch (error) {
        console.error("Error updating trade client:", error);
        Swal.fire(
          'Error!',
          'There was an error saving your changes.',
          'error'
        );
      }
    }
  };

  return (
    <div style={{ paddingTop: "20px" }}>
      <Card>
        <CardBody>
          <div className="container mt-5" style={{ paddingTop: "25px" }}>
            {/* Section A: Top-Left Heading */}
            <div
              className="mb-4"
              style={{ position: "absolute", top: "20px", left: "20px" }}
            >
              <h5 style={{ margin: 0, fontWeight: "bold", color: "black" }}>
                {formData.symbol}{" "}
                <span
                  style={{
                    color: formData.maxProfit > 0 ? "green" : "red",
                    fontWeight: "bold",
                  }}
                >
                  {/* Removed price */}
                </span>
              </h5>

            </div>

            {/* Section B: Dropdown Headings */}
            <Row className="mb-4">
              <Col md={2}>
                <Label>Symbol</Label>
                <Input
                  type="select"
                  name="symbol"
                  value={formData.symbol}
                  onChange={handleChange}
                >
                  <option value="" disabled>Select Symbol</option>
                  {symbols.map((shortName, index) => (
                    <option key={index} value={shortName}>
                      {shortName}
                    </option>
                  ))}
                </Input>
              </Col>

              <Col md={2}>
                <Label>Expiry</Label>
                <Input
                  type="select"
                  name="expiry"
                  id="expiry"
                  value={formData.expiry}
                  onChange={handleChange}
                >
                  <option value="" disabled>
                    Select Expiry
                  </option>
                  {expiryDates.map((date, index) => (
                    <option key={index} value={date}>
                      {date}
                    </option>
                  ))}
                </Input>
              </Col>

              <Col md={2}>
                <label htmlFor="groupService">Group Service</label>
                <Input
                  type="select"
                  name="groupService"
                  id="groupService"
                  value={formData.groupService}
                  onChange={handleChange}
                >
                  <option value="">Select Group Service</option>
                  {groupService.map((service, index) => (
                    <option key={index} value={service.name}>
                      {service.name}
                    </option>
                  ))}
                </Input>
              </Col>

              <Col md={2}>
                <Label htmlFor="broker">Broker</Label>
                <Input
                  type="select"
                  name="broker"
                  id="broker"
                  value={formData.broker}
                  onChange={(e) => setFormData({ ...formData, broker: e.target.value })}
                >
                  <option value="" disabled>Select Broker</option>
                  {brokerNames.length > 0 ? (
                    brokerNames.map((name, index) => (
                      <option key={index} value={name}>
                        {name}
                      </option>
                    ))
                  ) : (
                    <option value="">No Brokers Available</option>
                  )}
                </Input>
              </Col>

              <Col md={2}>
                <label>Product Type</label>
                <Input
                  type="select"
                  name="productType"
                  value={formData.productType}
                  onChange={handleChange}
                >
                  <option value="">Select Product Type</option>
                  <option value="MIS">MIS</option>
                  <option value="CNC">CNC</option>
                  <option value="NRML">NRML</option>
                </Input>
              </Col>
            </Row>

            {/* Section C: Table */}
            <div className="table-responsive-sm" style={{ overflowX: 'scroll' }}>
              <Table bordered>
                <thead>
                  <tr>
                    <th className="custom-col-design">Quantity</th>
                    <th className="custom-col-design">Stop-Loss</th>
                    <th className="custom-col-design">S/L Type</th>
                    <th className="custom-col-design">Target</th>
                    <th className="custom-col-design">Trade Limit</th>
                    <th className="custom-col-design">Max Loss For Day</th>
                    <th className="custom-col-design">Min Loss For Day</th>
                    <th className="custom-col-design">Max Profit For Day</th>
                    <th className="custom-col-design">Min Profit For Day</th>
                  </tr>
                </thead>
                <tbody>
                  {apiData.length > 0
                    ? apiData.map((item, index) => (
                      <tr key={index}>
                        <td>
                          <Input
                            style={{ width: '100px' }}
                            type="number"
                            name={`quantity`}
                            value={item.quantity || ""}
                            onChange={(e) => handleInputChange(e, index, "quantity")}
                            min="1"
                          />
                        </td>
                        <td>
                          <Input
                            style={{ width: '100px' }}
                            type="number"
                            name={`stopLoss`}
                            id="stopLoss"
                            value={item.stop_loss ?? ""}
                            onChange={(e) => handleInputChange(e, index, "stop_loss")}
                            min="1"
                          />
                        </td>
                        <td>
                          <Input
                            style={{ width: '120px' }}
                            type="select"
                            name="slType"
                            value={formData.slType}
                            onChange={handleChange}
                          >
                            <option value="">--</option>
                            <option value="Points">Points</option>
                            <option value="Percentage">Percentage</option>
                          </Input>
                        </td>
                        <td>
                          <Input
                            style={{ width: '100px' }}
                            type="number"
                            name={`target`}
                            value={item.target || ""}
                            onChange={(e) => handleInputChange(e, index, "target")}
                            min="1"
                          />
                        </td>
                        <td>
                          <Input
                            style={{ width: '100px' }}
                            type="number"
                            name={`tradeLimit`}
                            value={item.trade_limit || ""}
                            onChange={(e) => handleInputChange(e, index, "trade_limit")}
                          />
                        </td>
                        <td>
                          <Input
                            type="number"
                            name={`maxLoss`}
                            value={item.max_loss_for_day || ""}
                            onChange={(e) => handleInputChange(e, index, "max_loss_for_day")}
                          />
                        </td>
                        <td>
                          <Input
                            type="number"
                            name={`minLoss`}
                            value={item.min_loss_for_day || ""}
                            onChange={(e) => handleInputChange(e, index, "min_loss_for_day")}
                          />
                        </td>
                        <td>
                          <Input
                            type="number"
                            name={`maxProfit`}
                            value={item.max_profit_for_day || ""}
                            onChange={(e) => handleInputChange(e, index, "max_profit_for_day")}
                          />
                        </td>
                        <td>
                          <Input
                            type="number"
                            name={`minProfit`}
                            value={item.min_profit_for_day || ""}
                            onChange={(e) => handleInputChange(e, index, "min_profit_for_day")}
                          />
                        </td>
                      </tr>
                    ))
                    : (
                      <tr>
                        <td colSpan="7" className="text-center">
                          No data available. Please add new data.
                        </td>
                      </tr>
                    )}
                </tbody>
              </Table>
            </div>
            {/* Section D: Buttons */}
            <div className="d-flex justify-content-end mt-3">
              <Button color="danger" className="me-3" onClick={handleCancel}>
                Cancel
              </Button>
              <Button className="btn btn-primary search-btn-clr" onClick={handleOk}>
                Ok
              </Button>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default EditPage;