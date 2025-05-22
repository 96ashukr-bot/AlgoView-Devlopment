import React, { useState, useEffect } from "react";
import "./Clients.css";
import {
  getClientSegmentsList, getBroker, EnableDisableBroker, UpdateClientBroker, getClientApiStatus, getClientBrokerDetail
} from "../../../../Services/Authentication";
import Swal from 'sweetalert2';
import { getWebSocketUrl } from "../../../../ConfigUrl/config";
import useWebSocket from "react-use-websocket";
import {
  FormGroup, Label, Input, Modal, ModalHeader, ModalBody, ModalFooter, Button,
} from "reactstrap";

const ClientHeader = () => {
  const [segData, setSegData] = useState([]);
  const [visibleSegData, setVisibleSegData] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [webSocketUrl, setWebSocketUrl] = useState("");
  const [tokenPrices, setTokenPrices] = useState({});
  const [isToggleOn, setIsToggleOn] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [brokerList, setBrokerList] = useState([]);
  const [selectedBroker, setSelectedBroker] = useState("");
  const [brokerFields, setBrokerFields] = useState({});
  const [formErrors, setFormErrors] = useState({});
  const [brokerInput, setbrokerInput] = useState([]);
  const [brokerFieldMapping, setBrokerFieldMapping] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { lastMessage } = useWebSocket(webSocketUrl || null, {
    shouldReconnect: () => true,
    onError: (error) => console.error("WebSocket error:", error),
    onOpen: () => console.log('Header WebSocket connected'),
    onClose: () => console.log('Header WebSocket disconnected'),
  });

  useEffect(() => {
    fetchApiStatus();
    fetchClientSegments();
    fetchBrokerList();
  }, []);

  useEffect(() => {
    if (lastMessage !== null) {
      const messageData = JSON.parse(lastMessage.data);
      console.log('Received WebSocket header message :', messageData);
      if (messageData.token) {
        setTokenPrices((prevPrices) => ({
          ...prevPrices,
          [messageData.token]: {
            price: parseFloat(messageData.price.replace(/,/g, "")),
            trend: messageData.trend,
            difference: messageData.difference,
            percentage: messageData.percentage,
          },
        }));
      }
    }
  }, [lastMessage]);

  const fetchApiStatus = async () => {
    try {
      const status = await getClientApiStatus();
      console.log("API Status:", status);
      setIsToggleOn(status.is_enable);
    } catch (error) {
      console.error("Error fetching API status:", error);
    }
  };

  const fetchClientSegments = async () => {
    try {
      const response = await getClientSegmentsList();
      if (response.client_segment_list && response.client_segment_list.length > 0) {
        const transformedData = response.client_segment_list.map((item) => ({
          name: item.sub_segment.name,
          token: item.sub_segment.token,
          change:
            parseFloat(item.max_profit_for_day) -
            parseFloat(item.min_profit_for_day),
        }));
        setSegData(transformedData);
        setVisibleSegData(transformedData.slice(0, 3));
      } else {
        // Set default values if no data is returned
        if (!isExpanded) {
          setSegData([
            { name: "Nifty Fin Service", token: "NIFTY_FIN_SERVICE", change: 0 },
            { name: "Nifty 50", token: "NIFTY_50", change: 0 },
          ]);
        }
      }

      const Exchange = response.client_segment_list[0]?.sub_segment?.Exchange;
      const token = response.client_segment_list
        .map((item) => item.sub_segment.token)
        .join(",");
      // setWebSocketUrl(getWebSocketUrl(Exchange, token));

      const webSocketParams = [];
      if (Exchange) webSocketParams.push(Exchange);
      if (token) webSocketParams.push(token);

      if (webSocketParams.length > 0) {
        setWebSocketUrl(getWebSocketUrl(...webSocketParams));
      }

    } catch (error) {
      console.error("Error fetching client segments:", error);
      // Optionally set default values in case of an error
      if (!isExpanded) {
        setSegData([
          { name: "Nifty Fin Service", token: "NIFTY_FIN_SERVICE", change: 0 },
          { name: "Nifty 50", token: "NIFTY_50", change: 0 },
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleToggleMore = () => {
    if (!isExpanded) {
      // Show all unique items
      setVisibleSegData(segData);
    } else {
      // Show only the first 3 items
      setVisibleSegData(segData.slice(0, 3));
    }
    setIsExpanded(!isExpanded);
  };

  const fetchBrokerList = async () => {
    try {
      const brokers = await getBroker();
      setBrokerList(brokers);

      // Dynamically configure broker fields
      const dynamicBrokerFieldMapping = brokers.reduce((mapping, broker) => {
        const brokerName = broker.broker_name.toLowerCase().replace(/\s+/g, '').replace(/_/g, '');
        const brokerNames = broker.broker_name

        switch (brokerName) {
          case "fyers":
            mapping[brokerNames] = [
              { key: "broker_API_KEY", value: "API Key (ClientId)" },
              { key: "broker_API_SKEY", value: "API SKey" },
            ];
            break;

          case "angleone":
            mapping[brokerNames] = [
              { key: "broker_API_KEY", value: "API Key" },
              { key: "broker_Demate_User_Name", value: "User Client ID" },
              { key: "broker_Totp_Authcode", value: "TOTP Secret" },
              { key: "broker_pass", value: "Password" },
            ];
            break;

          case "aliceblue":
            mapping[brokerNames] = [
              { key: "broker_API_KEY", value: "API Key" },
              { key: "broker_API_UID", value: "API UID" },
            ];
            break;

          case "zerodha":
            mapping[brokerNames] = [
              { key: "broker_API_KEY", value: "API Key" },
              { key: "broker_API_SKEY", value: "API Secret Key" },
            ];
            break;

          case "upstox":
            mapping[brokerNames] = [
              { key: "broker_API_KEY", value: "API Key" },
              { key: "broker_API_SKEY", value: "API SKey" },
            ];
            break;

          case "5paisa":
            mapping[brokerNames] = [
              { key: "broker_API_KEY", value: "API Key (User Key)" },
              { key: "broker_API_SKEY", value: "API SKey (Encryption Key)" },
              { key: "broker_API_UID", value: "API UID (User Id)" },
            ];
            break;

          case "dhan":
            mapping[brokerNames] = [
              { key: "broker_API_KEY", value: "API Key" },
              { key: "access_token", value: "Access Token" },
            ];
            break;

          default:
            mapping[brokerNames] = [
              { key: "broker_API_KEY", value: "API Key" },
            ];
        }

        return mapping;
      }, {});

      setBrokerFieldMapping(dynamicBrokerFieldMapping);
    } catch (error) {
      console.error("Error fetching broker list:", error);
    }
  };

  const handleToggle = async () => {
    try {
      const newToggleState = !isToggleOn;
      setIsToggleOn(newToggleState);

      const response = await EnableDisableBroker({ is_enable: newToggleState });

      if (!isToggleOn) {
        setIsModalOpen(true);

        const brokerDetails = await getClientBrokerDetail();
        if (brokerDetails && brokerDetails.data) {
          const { broker_name, broker_API_KEY, broker_API_SKEY, broker_API_UID, broker_Demate_User_Name, broker_Totp_Authcode, broker_pass } = brokerDetails.data;
          console.log('ssss', brokerDetails.data);
          setSelectedBroker(broker_name.broker_name);
          setBrokerFields(brokerFieldMapping[broker_name.broker_name] || []);

          setbrokerInput(brokerDetails.data);
        }
      }
    } catch (error) {
      console.error("Error enabling/disabling broker:", error);
    }
  };

  const closeModal = () => setIsModalOpen(false);

  const handleBrokerChange = (e) => {
    const brokerName = e.target.value;
    setSelectedBroker(brokerName);
    setBrokerFields(brokerFieldMapping[brokerName] || []);
    setFormErrors({});
    setbrokerInput({});
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;

    console.log('e.target', name, value);
    setFormErrors((prevErrors) => ({ ...prevErrors, [name]: !value.trim() }));
    setbrokerInput((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const validateForm = () => {
    const errors = {};
    brokerFields.forEach((field) => {
      const value = brokerInput[field.key] || "";
      errors[field.key] = !value.trim();
    });
    setFormErrors(errors);
    return Object.values(errors).every((error) => !error);
  };

  const handleUpdate = async (e) => {
    e.stopPropagation();
    if (isSubmitting) return;
    setIsSubmitting(true);

    if (validateForm()) {
      const payload = {};
      const selectedBrokerData = brokerList.find(
        (broker) => broker.broker_name === selectedBroker
      );
      if (selectedBrokerData) {
        payload.broker_name = selectedBrokerData.id;
      }

      brokerFields.forEach(({ key }) => {
        payload[key] = brokerInput[key] || "";
      });

      try {
        const response = await UpdateClientBroker(payload);
        Swal.fire('Success', 'Broker updated successfully!', 'success');
        closeModal();
      } catch (error) {
        console.error("Error updating broker details:", error);
        Swal.fire('Error', 'Broker update failed: Invalid response', 'error');
      }
    }
    setIsSubmitting(false);
  };

  const getColor = (trend) => {
    if (trend === "+") return "text-success";
    if (trend === "-") return "text-danger";
    return "text-muted";
  };

  return (
    <div className="client-header">
      <div
        className="header-controls header-custom-control"

      >
        <h4 className="bold head-style" style={{ marginBottom: "-8px" }}>
          Select Broker
        </h4>
        <FormGroup switch className="mt-2 switch-toggle-custom">
          <Input
            style={{ width: "50px", height: "25px", border: "1px solid gray" }}
            type="checkbox"
            name="switchOption"
            id="switchOption"
            checked={isToggleOn}
            onChange={handleToggle}
          />
        </FormGroup>
      </div>
      {loading ? (
        <p>Loading...</p>
      ) : (

        <div className="nifty-data">
          {/* First row for default visible items */}
          <div className="nifty-visible">
            {segData.slice(0, 3).map((item, index) => {
              const tokenData = tokenPrices[item.token] || {};
              const { price, trend, difference, percentage } = tokenData;
              const colorClass = getColor(trend);

              return (
                <div key={index} className="nifty-item">
                  <span className="nifty-name bold">{item.name}</span>
                  <span className={`nifty-value bold ${colorClass}`}>
                    {price ? price.toFixed(2) : "00.0"}
                  </span>
                  <span className={`nifty-difference bold ${colorClass}`}>
                    {difference || "0"}
                  </span>
                  <span className={`nifty-percentage bold ${colorClass}`}>
                    {percentage || "(0%)"}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Second row for expanded items */}
          {isExpanded && (
            <div className="nifty-hidden">
              {segData.slice(3).map((item, index) => {
                const tokenData = tokenPrices[item.token] || {};
                const { price, trend, difference, percentage } = tokenData;
                const colorClass = getColor(trend);

                return (
                  <div key={index + 3} className="nifty-item">
                    <span className="nifty-name bold">{item.name}</span>
                    <span className={`nifty-value bold ${colorClass}`}>
                      {price ? price.toFixed(2) : "00.0"}
                    </span>
                    <span className={`nifty-difference bold ${colorClass}`}>
                      {difference || "0"}
                    </span>
                    <span className={`nifty-percentage bold ${colorClass}`}>
                      {percentage || "(0%)"}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Button to toggle more/less */}
          {segData.length > 3 && (
            <button onClick={handleToggleMore} className="toggle-button">
              {isExpanded ? "Show Less" : "Show More"}
            </button>
          )}
        </div>

      )}

      {/* Modal Component */}
      <Modal isOpen={isModalOpen} toggle={closeModal}>
        <ModalHeader toggle={closeModal}>Broker Selection</ModalHeader>
        <ModalBody>
          <FormGroup>
            <Label for="brokerSelect">Select a Broker</Label>
            <Input
              type="select"
              id="brokerSelect"
              value={selectedBroker}
              onChange={handleBrokerChange}
            >
              <option value="">-- Select a Broker --</option>
              {brokerList.map((broker) => (
                <option key={broker.id} value={broker.broker_name}>
                  {broker.broker_name}
                </option>
              ))}
            </Input>
          </FormGroup>
          {brokerFields.length > 0 && (
            <div className="broker-fields">
              {brokerFields.map((field, index) => (
                <FormGroup key={index}>
                  <Label for={field.key}>{field.value}</Label>
                  <Input
                    type="text"
                    id={field.key}
                    name={field.key}
                    placeholder={`Enter ${field.value}`}
                    // value={brokerFields[field.key] || ""}
                    value={brokerInput[field.key] || ""}
                    className={formErrors[field.key] ? "is-invalid" : ""}
                    onChange={handleInputChange}
                  />
                  {formErrors[field.key] && (
                    <div className="invalid-feedback">
                      {`${field.value} is required.`}
                    </div>
                  )}
                </FormGroup>
              ))}

            </div>
          )}

        </ModalBody>
        <ModalFooter>
          <Button className="search-btn-clr" onClick={handleUpdate}>
            Update
          </Button>
          <Button
            color="danger"
            onClick={closeModal}
            style={{ marginLeft: "10px" }}
          >
            Cancel
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default ClientHeader;