import React, { useState, useEffect } from "react";
import "./Clients.css";
import {
  getClientSegmentsList,
  getBroker,
  getClientApiStatus,
  UpdateClientBroker,
  getClientBrokerDetail,
  startBrokerConnectFlow,
  getBrokerRuntimeStatus,
  generateBrokerToken,
  getMyExecutionNode,
  saveMyExecutionNode,
  releaseMyExecutionNode,
  verifyMyExecutionProxy,
} from "../../../../Services/Authentication";
import Swal from 'sweetalert2';
import { getWebSocketUrl } from "../../../../ConfigUrl/config";
import useWebSocket from "react-use-websocket";
import {
  FormGroup, Label, Input, Modal, ModalHeader, ModalBody, ModalFooter, Button,
} from "reactstrap";

const brokerSchemaFallbacks = {
  "angel one": {
    display_name: "Angel One",
    auth_mode: "direct_credentials",
    description: "Store Angel One credentials securely, then use the daily broker login flow to create a trading session.",
    save_action_label: "Save Broker Name API Details",
    connect_action_label: "Generate Angel One Token",
    connect_path: "/broker_auth_login/?broker=angel%20one",
    supports_callback: true,
    supports_redirect: true,
    fields: [
      { key: "broker_API_KEY", label: "API Key", type: "password", required: true, secret: true },
      { key: "broker_Demate_User_Name", label: "Client ID / User ID", type: "text", required: true, secret: false },
      { key: "broker_pass", label: "Password", type: "password", required: true, secret: true },
      { key: "broker_Totp_Authcode", label: "TOTP Secret", type: "password", required: true, secret: true },
    ],
  },
  "upstox": {
    display_name: "Upstox",
    auth_mode: "redirect_oauth",
    description: "Save the Upstox API credentials, then use the broker redirect flow to connect the account.",
    save_action_label: "Save Broker Name API Details",
    connect_action_label: "Connect to Upstox",
    connect_path: "/broker_auth_login/?broker=upstox",
    supports_callback: true,
    supports_redirect: true,
    fields: [
      { key: "broker_API_KEY", label: "API Key", type: "password", required: true, secret: true },
      { key: "broker_API_SKEY", label: "API Secret Key", type: "password", required: true, secret: true },
    ],
  },
  "zerodha": {
    display_name: "Zerodha",
    auth_mode: "redirect_oauth",
    description: "Save Zerodha API credentials, then complete the broker-side login flow from the trading panel.",
    save_action_label: "Save Broker Name API Details",
    connect_action_label: "Connect to Zerodha",
    connect_path: "/broker_auth_login/?broker=zerodha",
    supports_callback: false,
    supports_redirect: true,
    fields: [
      { key: "broker_API_KEY", label: "API Key", type: "password", required: true, secret: true },
      { key: "broker_API_SKEY", label: "API Secret Key", type: "password", required: true, secret: true },
    ],
  },
  "alice blue": {
    display_name: "Alice Blue",
    auth_mode: "redirect_oauth",
    description: "Save Alice Blue User ID, App Code/API Key, and App Secret, then complete Alice's ANT auth-code flow through the assigned execution proxy/static IP.",
    save_action_label: "Save Broker Name API Details",
    connect_action_label: "Connect to Alice Blue",
    connect_path: "/broker_auth_login/?broker=alice%20blue",
    supports_callback: true,
    supports_redirect: true,
    fields: [
      { key: "broker_API_UID", label: "User ID", type: "text", required: true, secret: false },
      { key: "broker_API_KEY", label: "App Code / API Key", type: "password", required: true, secret: true },
      { key: "broker_API_SKEY", label: "App Secret / API Secret", type: "password", required: true, secret: true },
    ],
    requirement_note: "Click Connect to Alice Blue after saving credentials. Alice opens ANT login with appcode, returns authCode to AlgoView, and AlgoView exchanges it for the daily session through the assigned proxy/static IP.",
  },
  "5paisa": {
    display_name: "5Paisa",
    auth_mode: "redirect_oauth",
    description: "Save the 5Paisa API credentials used for daily login/session generation.",
    save_action_label: "Save Broker Name API Details",
    connect_action_label: "Connect to 5Paisa",
    connect_path: "/broker_auth_login/?broker=5paisa",
    supports_callback: false,
    supports_redirect: true,
    fields: [
      { key: "broker_API_KEY", label: "User Key", type: "password", required: true, secret: true },
      { key: "broker_API_SKEY", label: "Encryption Key", type: "password", required: true, secret: true },
      { key: "broker_API_UID", label: "User ID", type: "text", required: true, secret: false },
    ],
  },
  "fyers": {
    display_name: "FYERS",
    auth_mode: "redirect_oauth",
    description: "Save FYERS API credentials, then complete the broker login flow from the trading panel.",
    save_action_label: "Save Broker Name API Details",
    connect_action_label: "Connect to FYERS",
    connect_path: "/broker_auth_login/?broker=fyers",
    supports_callback: false,
    supports_redirect: true,
    fields: [
      { key: "broker_API_KEY", label: "Client ID", type: "password", required: true, secret: true },
      { key: "broker_API_SKEY", label: "Secret Key", type: "password", required: true, secret: true },
    ],
  },
  "dhan": {
    display_name: "Dhan",
    auth_mode: "redirect_oauth",
    description: "Use either a Dhan Web access token, or save App/API Key + Secret + Client ID and complete Dhan's consent flow.",
    save_action_label: "Save Broker Name API Details",
    connect_action_label: "Connect to Dhan",
    connect_path: "/broker_auth_login/?broker=dhan",
    supports_callback: true,
    supports_redirect: true,
    fields: [
      { key: "broker_API_KEY", label: "App ID / API Key", type: "password", required: false, secret: true },
      { key: "broker_API_SKEY", label: "App Secret / API Secret", type: "password", required: false, secret: true },
      { key: "broker_API_UID", label: "Dhan Client ID", type: "text", required: false, secret: false },
      { key: "access_token", label: "Access Token", type: "password", required: false, secret: true },
    ],
    requirement_note: "Provide either Access Token, or App/API Key + Secret + Dhan Client ID for consent login.",
  },
};

const normalizeBrokerName = (name) => {
  if (!name) return "";
  const normalized = String(name).trim().toLowerCase().replace(/[_-]/g, " ").replace(/\s+/g, " ");
  if (["angle one", "angleone", "angelone"].includes(normalized)) {
    return "angel one";
  }
  if (["aliceblue", "alice blue"].includes(normalized)) {
    return "alice blue";
  }
  if (["5 paisa", "five paisa"].includes(normalized)) {
    return "5paisa";
  }
  return normalized;
};

const ClientHeader = () => {
  const [segData, setSegData] = useState([]);
  const [visibleSegData, setVisibleSegData] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [webSocketUrl, setWebSocketUrl] = useState("");
  const [tokenPrices, setTokenPrices] = useState({});
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [brokerList, setBrokerList] = useState([]);
  const [selectedBroker, setSelectedBroker] = useState("");
  const [brokerFields, setBrokerFields] = useState([]);
  const [brokerSetup, setBrokerSetup] = useState(null);
  const [setupStep, setSetupStep] = useState("select");
  const [formErrors, setFormErrors] = useState({});
  const [brokerInput, setbrokerInput] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [touchedBrokerFields, setTouchedBrokerFields] = useState({});
  const [existingSelectedBroker, setExistingSelectedBroker] = useState("");
  const [brokerRuntimeStatus, setBrokerRuntimeStatus] = useState({
    session: { status: "unavailable", is_active: false },
    token: { status: "unavailable", is_active: false, is_expired: false, expires_at: null },
    last_login_at: null,
    last_logout_at: null,
    auth_mode: null,
  });
  const [isExecutionModalOpen, setIsExecutionModalOpen] = useState(false);
  const [executionNode, setExecutionNode] = useState(null);
  const [executionNodeInput, setExecutionNodeInput] = useState({
    execution_type: "vps_node",
    name: "",
    ip_address: "",
    provider: "",
    server_url: "",
    node_id: "",
    node_secret: "",
    proxy_protocol: "http",
    proxy_host: "",
    proxy_port: "",
    proxy_username: "",
    proxy_password: "",
    is_active: true,
  });
  const [isExecutionSaving, setIsExecutionSaving] = useState(false);
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
    fetchClientExecutionNode();
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
      await fetchSavedBrokerDetails(brokers);
      await fetchBrokerRuntime();
    } catch (error) {
      console.error("Error fetching broker list:", error);
    }
  };

  const fetchBrokerRuntime = async () => {
    try {
      const runtime = await getBrokerRuntimeStatus();
      setBrokerRuntimeStatus(runtime);
      window.dispatchEvent(new CustomEvent("broker-runtime-updated", { detail: runtime }));
    } catch (error) {
      console.error("Error fetching broker runtime status:", error);
    }
  };

  const fetchClientExecutionNode = async () => {
    try {
      const response = await getMyExecutionNode();
      const node = response?.node || null;
      setExecutionNode(node);
      setExecutionNodeInput({
        name: node?.name || "",
        execution_type: node?.execution_type || "vps_node",
        ip_address: node?.ip_address || "",
        provider: node?.provider || "",
        server_url: node?.server_url || "",
        node_id: node?.node_id || "",
        node_secret: "",
        proxy_protocol: node?.proxy_protocol || "http",
        proxy_host: node?.proxy_host || "",
        proxy_port: node?.proxy_port || "",
        proxy_username: node?.proxy_username || "",
        proxy_password: "",
        is_active: node?.is_active ?? true,
      });
    } catch (error) {
      console.error("Error fetching client execution node:", error);
    }
  };

  const openExecutionModal = async () => {
    setIsExecutionModalOpen(true);
    await fetchClientExecutionNode();
  };

  const closeExecutionModal = () => {
    setIsExecutionModalOpen(false);
  };

  const handleExecutionInputChange = (event) => {
    const { name, value, type, checked } = event.target;
    setExecutionNodeInput((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSaveExecutionNode = async () => {
    const isProxy = executionNodeInput.execution_type === "proxy";
    const requiredFields = isProxy
      ? ["name", "ip_address", "proxy_protocol", "proxy_host", "proxy_port"]
      : ["name", "ip_address", "server_url", "node_id"];
    const missingField = requiredFields.find((field) => !String(executionNodeInput[field] || "").trim());
    if (missingField) {
      Swal.fire("Error", "Please fill node name, static IP, server URL, and node ID.", "error");
      return;
    }
    if (!isProxy && !executionNode && !String(executionNodeInput.node_secret || "").trim()) {
      Swal.fire("Error", "Please add node secret when creating a new execution IP.", "error");
      return;
    }

    setIsExecutionSaving(true);
    try {
      const payload = {
        name: executionNodeInput.name.trim(),
        execution_type: executionNodeInput.execution_type,
        ip_address: executionNodeInput.ip_address.trim(),
        provider: executionNodeInput.provider.trim(),
        is_active: executionNodeInput.is_active,
      };
      if (isProxy) {
        payload.proxy_protocol = executionNodeInput.proxy_protocol;
        payload.proxy_host = executionNodeInput.proxy_host.trim();
        payload.proxy_port = executionNodeInput.proxy_port;
        payload.proxy_username = executionNodeInput.proxy_username.trim();
      } else {
        payload.server_url = executionNodeInput.server_url.trim();
        payload.node_id = executionNodeInput.node_id.trim();
      }
      if (!isProxy && executionNodeInput.node_secret) {
        payload.node_secret = executionNodeInput.node_secret;
      }
      if (isProxy && executionNodeInput.proxy_password) {
        payload.proxy_password = executionNodeInput.proxy_password;
      }
      const savedNode = await saveMyExecutionNode(payload, Boolean(executionNode));
      setExecutionNode(savedNode);
      setExecutionNodeInput((previous) => ({ ...previous, node_secret: "" }));
      Swal.fire("Success", "Execution IP saved successfully.", "success");
      await fetchClientExecutionNode();
    } catch (error) {
      Swal.fire("Error", error.message || "Failed to save execution IP.", "error");
    } finally {
      setIsExecutionSaving(false);
    }
  };

  const handleReleaseExecutionNode = async () => {
    const confirmation = await Swal.fire({
      title: "Release execution IP?",
      text: "Live routed orders will be blocked until another verified execution IP is assigned.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Yes, release",
      cancelButtonText: "Cancel",
    });
    if (!confirmation.isConfirmed) {
      return;
    }
    setIsExecutionSaving(true);
    try {
      await releaseMyExecutionNode();
      setExecutionNode(null);
      setExecutionNodeInput({
        name: "",
        execution_type: "vps_node",
        ip_address: "",
        provider: "",
        server_url: "",
        node_id: "",
        node_secret: "",
        proxy_protocol: "http",
        proxy_host: "",
        proxy_port: "",
        proxy_username: "",
        proxy_password: "",
        is_active: true,
      });
      Swal.fire("Success", "Execution IP released.", "success");
    } catch (error) {
      Swal.fire("Error", error.message || "Failed to release execution IP.", "error");
    } finally {
      setIsExecutionSaving(false);
    }
  };

  const handleVerifyExecutionProxy = async () => {
    setIsExecutionSaving(true);
    try {
      const response = await verifyMyExecutionProxy();
      await fetchClientExecutionNode();
      const result = response?.result || {};
      Swal.fire(result.status === "success" ? "Success" : "Error", result.message || "Proxy verification completed.", result.status === "success" ? "success" : "error");
    } catch (error) {
      Swal.fire("Error", error.message || "Failed to verify proxy IP.", "error");
    } finally {
      setIsExecutionSaving(false);
    }
  };

  const fetchSavedBrokerDetails = async (availableBrokers = brokerList) => {
    try {
      const brokerDetails = await getClientBrokerDetail();
      if (brokerDetails?.data) {
        const payload = brokerDetails.data.available_brokers?.length
          ? brokerDetails.data
          : {
              ...brokerDetails.data,
              available_brokers: availableBrokers,
            };
        applyBrokerDetails(payload);
      }
    } catch (error) {
      console.error("Error fetching client broker detail:", error);
    }
  };

  const getBrokerDefinition = (brokerName, availableBrokers = brokerList) => {
    const normalizedSelected = normalizeBrokerName(brokerName);
    return availableBrokers.find((broker) => normalizeBrokerName(broker.broker_name) === normalizedSelected);
  };

  const buildFallbackSchema = (brokerName, currentInput = {}) => {
    const fallback = brokerSchemaFallbacks[normalizeBrokerName(brokerName)];
    if (!fallback) {
      return null;
    }
    return {
      ...fallback,
      fields: fallback.fields.map((field) => {
        const currentValue = currentInput[field.key];
        const configured = typeof currentValue === "string" ? Boolean(currentValue.trim()) : Boolean(currentValue);
        return {
          ...field,
          configured,
          persisted: configured,
          value: field.secret ? null : (currentValue || null),
          display_value: field.secret ? (configured ? "Saved" : null) : (currentValue || null),
        };
      }),
    };
  };

  const buildBrokerInputFromResponse = (brokerData, schema) => {
    const nextInput = {};
    if (brokerData?.broker_API_UID) {
      nextInput.broker_API_UID = brokerData.broker_API_UID;
    }
    if (brokerData?.broker_Demate_User_Name) {
      nextInput.broker_Demate_User_Name = brokerData.broker_Demate_User_Name;
    }
    (schema?.fields || []).forEach((field) => {
      if (!field.secret && typeof field.value === "string") {
        nextInput[field.key] = field.value;
      }
    });
    return nextInput;
  };

  const applyBrokerDetails = (brokerData) => {
    const availableBrokers = brokerData?.available_brokers?.length ? brokerData.available_brokers : brokerList;
    if (brokerData?.available_brokers?.length) {
      setBrokerList(brokerData.available_brokers);
    }

    const selectedName = brokerData?.selected_broker_name || brokerData?.broker_name?.broker_name || "";
    const selectedDefinition = selectedName ? getBrokerDefinition(selectedName, availableBrokers) : null;
    const selectedSchema = brokerData?.broker_setup || selectedDefinition?.setup_schema || buildFallbackSchema(selectedName, brokerData);

    const selectedDisplayName = selectedSchema?.display_name || selectedName;
    setSelectedBroker(selectedDisplayName);
    setExistingSelectedBroker(selectedDisplayName);
    setBrokerSetup(selectedSchema);
    setBrokerFields(selectedSchema?.fields || []);
    setbrokerInput(buildBrokerInputFromResponse(brokerData, selectedSchema));
    setTouchedBrokerFields({});
    setFormErrors({});
    setSetupStep(selectedName ? "configure" : "select");
  };

  const openBrokerSetupModal = async () => {
    setIsModalOpen(true);
    await fetchSavedBrokerDetails();
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSetupStep(existingSelectedBroker ? "configure" : "select");
    setFormErrors({});
  };

  const handleBrokerChange = (e) => {
    const brokerName = e.target.value;
    const definition = getBrokerDefinition(brokerName);
    const schema = definition?.setup_schema || buildFallbackSchema(brokerName, brokerInput);
    setSelectedBroker(schema?.display_name || brokerName);
    setBrokerSetup(schema);
    setBrokerFields(schema?.fields || []);
    setFormErrors({});
    if (brokerName === existingSelectedBroker && brokerSetup) {
      setbrokerInput((prevData) => ({ ...prevData }));
    } else {
      setbrokerInput({});
    }
    setTouchedBrokerFields({});
    setSetupStep(brokerName ? "configure" : "select");
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;

    console.log('e.target', name, value);
    setFormErrors((prevErrors) => ({ ...prevErrors, [name]: !value.trim() }));
    setbrokerInput((prevData) => ({
      ...prevData,
      [name]: value,
    }));
    setTouchedBrokerFields((prevState) => ({
      ...prevState,
      [name]: true,
    }));
  };

  const existingFieldPresence = (fieldKey) => {
    const configuredField = brokerFields.find((field) => field.key === fieldKey);
    if (configuredField?.configured) {
      return true;
    }
    const rawValue = brokerInput[fieldKey];
    return typeof rawValue === "string" ? Boolean(rawValue.trim()) : Boolean(rawValue);
  };

  const hasSelectedBrokerSaved = Boolean(existingSelectedBroker)
    && normalizeBrokerName(existingSelectedBroker) === normalizeBrokerName(selectedBroker);

  const areRequiredBrokerFieldsReady = brokerFields.every((field) => {
    if (!field.required) {
      return true;
    }
    return existingFieldPresence(field.key);
  });

  const getDhanCredentialState = () => {
    const hasManualToken = existingFieldPresence("access_token");
    const hasConsentCredentials = ["broker_API_KEY", "broker_API_SKEY", "broker_API_UID"].every(existingFieldPresence);
    return { hasManualToken, hasConsentCredentials, isReady: hasManualToken || hasConsentCredentials };
  };

  const hasBrokerDetailsToSave = (() => {
    if (!selectedBroker) {
      return false;
    }
    const selectedBrokerData = getBrokerDefinition(selectedBroker);
    if (!selectedBrokerData) {
      return false;
    }
    const brokerSelectionChanged = !hasSelectedBrokerSaved;
    if (brokerSelectionChanged) {
      return true;
    }
    return brokerFields.some(({ key }) => {
      const rawValue = brokerInput[key];
      const normalizedValue = typeof rawValue === "string" ? rawValue.trim() : rawValue;
      return Boolean(touchedBrokerFields[key] && normalizedValue);
    });
  })();

  const validateForm = () => {
    const errors = {};
    if (!selectedBroker) {
      errors.broker_name = true;
    }
    brokerFields.forEach((field) => {
      if (!field.required) {
        errors[field.key] = false;
        return;
      }
      const value = typeof brokerInput[field.key] === "string" ? brokerInput[field.key].trim() : brokerInput[field.key];
      errors[field.key] = !value && !existingFieldPresence(field.key);
    });
    setFormErrors(errors);
    return Object.values(errors).every((error) => !error);
  };

  const buildBrokerPayload = () => {
    const payload = {};
    const selectedBrokerData = brokerList.find(
      (broker) => normalizeBrokerName(broker.broker_name) === normalizeBrokerName(selectedBroker)
    );
    if (selectedBrokerData) {
      payload.broker_name = selectedBrokerData.id;
    }

    brokerFields.forEach(({ key }) => {
      const rawValue = brokerInput[key];
      const normalizedValue = typeof rawValue === "string" ? rawValue.trim() : rawValue;
      if (touchedBrokerFields[key] && normalizedValue) {
        payload[key] = normalizedValue;
      }
    });

    return payload;
  };

  const handleSaveSelectedBroker = async () => {
    if (!selectedBroker) {
      setFormErrors({ broker_name: true });
      return;
    }

    const selectedBrokerData = getBrokerDefinition(selectedBroker);
    if (!selectedBrokerData) {
      Swal.fire('Error', 'Selected broker is not available.', 'error');
      return;
    }

    if (existingSelectedBroker && existingSelectedBroker !== selectedBroker) {
      const confirmation = await Swal.fire({
        title: 'Switch broker configuration?',
        text: `Changing the selected broker will keep the old credentials stored, but this client will now use ${selectedBroker}.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, switch broker',
        cancelButtonText: 'Cancel',
      });
      if (!confirmation.isConfirmed) {
        return;
      }
    }

    setIsSubmitting(true);
    try {
      const response = await UpdateClientBroker({ broker_name: selectedBrokerData.id });
      applyBrokerDetails(response.data || {});
      await fetchBrokerRuntime();
      setSetupStep("configure");
      Swal.fire('Success', `Broker selected: ${selectedBroker}`, 'success');
    } catch (error) {
      console.error("Error saving selected broker:", error);
      Swal.fire('Error', error.message || 'Failed to save selected broker.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDashboardBrokerConnect = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    try {
      let brokerData = null;
      let activeSchema = brokerSetup;
      let activeBrokerName = existingSelectedBroker || selectedBroker;

      if (!activeBrokerName || !activeSchema) {
        const brokerDetails = await getClientBrokerDetail();
        brokerData = brokerDetails?.data || {};
        if (brokerData) {
          applyBrokerDetails(brokerData);
          activeSchema = brokerData?.broker_setup || brokerSetup;
          activeBrokerName = brokerData?.selected_broker_name || existingSelectedBroker || selectedBroker;
        }
      }

      const normalizedActiveBroker = normalizeBrokerName(activeBrokerName);

      if (!activeBrokerName) {
        Swal.fire('Error', 'Please select and save a broker first.', 'error');
        setIsModalOpen(true);
        return;
      }

      if (normalizedActiveBroker === "angel one") {
        const connectResponse = await startBrokerConnectFlow("/broker_auth_login/?broker=angel%20one");
        window.location.assign(connectResponse.redirect_url);
        return;
      }

      if (activeSchema?.auth_mode === "direct_credentials") {
        const tokenResponse = await generateBrokerToken();
        if (tokenResponse?.action === "redirect" && tokenResponse?.redirect_url) {
          window.location.assign(tokenResponse.redirect_url);
          return;
        }
        if (tokenResponse?.data) {
          setBrokerRuntimeStatus((prev) => ({ ...prev, ...tokenResponse.data }));
          window.dispatchEvent(new CustomEvent("broker-runtime-updated", { detail: tokenResponse.data }));
        }
        await fetchBrokerRuntime();
        Swal.fire('Success', tokenResponse?.message || 'Broker token generated successfully.', 'success');
        return;
      }

      if (!activeSchema?.connect_path) {
        Swal.fire('Info', `${activeBrokerName} does not require daily token generation from this dashboard.`, 'info');
        return;
      }

      const missingRequiredFields = (activeSchema.fields || [])
        .filter((field) => field.required && !field.configured && !field.persisted && !field.value)
        .map((field) => field.label);

      if (normalizedActiveBroker === "dhan") {
        const { hasConsentCredentials } = getDhanCredentialState();
        if (!hasConsentCredentials) {
          Swal.fire('Error', 'For Dhan consent login, save App/API Key, App Secret/API Secret, and Dhan Client ID first. If you already have a Dhan access token, save it and no Connect to Dhan step is needed.', 'error');
          setIsModalOpen(true);
          return;
        }
      }

      if (missingRequiredFields.length > 0) {
        Swal.fire('Error', `Please save the required broker details first: ${missingRequiredFields.join(', ')}`, 'error');
        setIsModalOpen(true);
        return;
      }

      const connectResponse = await startBrokerConnectFlow(activeSchema.connect_path);
      window.location.assign(connectResponse.redirect_url);
    } catch (error) {
      Swal.fire('Error', error.message || 'Failed to start broker login.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdate = async (e) => {
    e.stopPropagation();
    if (isSubmitting) return;
    setIsSubmitting(true);

    if (validateForm()) {
      const payload = buildBrokerPayload();

      try {
        const response = await UpdateClientBroker(payload);
        if (response?.data) {
          applyBrokerDetails(response.data);
        }
        await fetchBrokerRuntime();
        Swal.fire('Success', response?.message || 'Broker updated successfully!', 'success');
      } catch (error) {
        console.error("Error updating broker details:", error);
        Swal.fire('Error', error.message || 'Broker update failed.', 'error');
      }
    }
    setIsSubmitting(false);
  };

  const getColor = (trend) => {
    if (trend === "+") return "text-success";
    if (trend === "-") return "text-danger";
    return "text-muted";
  };

  const currentBrokerDisplayName = existingSelectedBroker || selectedBroker || "";
  const currentBrokerDefinition = currentBrokerDisplayName
    ? getBrokerDefinition(currentBrokerDisplayName)
    : null;
  const currentBrokerSchema = brokerSetup || currentBrokerDefinition?.setup_schema || buildFallbackSchema(currentBrokerDisplayName);
  const dashboardConnectLabel = currentBrokerSchema?.connect_action_label || "Generate Token";
  const runtimeSessionStatus = brokerRuntimeStatus?.session?.status || "unavailable";
  const runtimeTokenStatus = brokerRuntimeStatus?.token?.status || "unavailable";
  const isRuntimeActive = Boolean(
    brokerRuntimeStatus?.session?.is_active || brokerRuntimeStatus?.token?.is_active
  );
  const runtimeBadgeStyles = {
    backgroundColor: isRuntimeActive ? "#dcfce7" : "#fee2e2",
    color: isRuntimeActive ? "#166534" : "#b91c1c",
    borderRadius: "999px",
    padding: "6px 10px",
    fontWeight: 700,
    fontSize: "12px",
    border: `1px solid ${isRuntimeActive ? "#86efac" : "#fca5a5"}`,
  };

  return (
    <div className="client-header">
      <div
        className="header-controls header-custom-control"

      >
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <h4 className="bold head-style" style={{ marginBottom: 0 }}>
            Broker
          </h4>
          <div style={{ color: "#6b7280", fontSize: "13px" }}>
            {currentBrokerDisplayName
              ? `Saved broker: ${currentBrokerDisplayName}`
              : "No broker selected yet"}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <Button className="search-btn-clr" onClick={openBrokerSetupModal}>
            {currentBrokerDisplayName ? `Choose Broker (${currentBrokerDisplayName})` : "Choose Broker"}
          </Button>
          <Button
            color="info"
            onClick={handleDashboardBrokerConnect}
            disabled={isSubmitting || !currentBrokerDisplayName || (!currentBrokerSchema?.connect_path && currentBrokerSchema?.auth_mode !== "direct_credentials")}
          >
            {dashboardConnectLabel}
          </Button>
          <Button color="secondary" outline onClick={openExecutionModal}>
            Execution IP
          </Button>
          <span style={runtimeBadgeStyles}>
            {isRuntimeActive ? "Active" : "Inactive"}
          </span>
        </div>
      </div>
      {loading ? (
        <p>Loading...</p>
      ) : (

        <div className="nifty-data">
          {/* First row for default visible items */}
          <div className="nifty-visible">
            {visibleSegData.slice(0, 3).map((item, index) => {
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
              {visibleSegData.slice(3).map((item, index) => {
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
        <ModalHeader toggle={closeModal}>Broker Setup</ModalHeader>
        <ModalBody>
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontWeight: 700, marginBottom: "6px" }}>Step 1: Select Broker</div>
            <div style={{ color: "#6b7280", fontSize: "14px" }}>
              Choose the broker first. Once selected, AlgoView will show only the fields and login flow required for that broker.
            </div>
          </div>
          <FormGroup>
            <Label for="brokerSelect">Select a Broker</Label>
            <Input
              type="select"
              id="brokerSelect"
              value={selectedBroker}
              onChange={handleBrokerChange}
              className={formErrors.broker_name ? "is-invalid" : ""}
            >
              <option value="">-- Select a Broker --</option>
              {brokerList.map((broker) => (
                <option key={broker.id} value={broker.broker_name}>
                  {broker.broker_name}
                </option>
              ))}
            </Input>
            {formErrors.broker_name && (
              <div className="invalid-feedback d-block">Broker selection is required.</div>
            )}
          </FormGroup>

          {selectedBroker && brokerSetup && (
            <div
              style={{
                background: "#f8fafc",
                border: "1px solid #e5e7eb",
                borderRadius: "12px",
                padding: "14px 16px",
                marginBottom: "16px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
                <div>
                  <div style={{ fontWeight: 700 }}>{selectedBroker}</div>
                  <div style={{ color: "#6b7280", fontSize: "14px" }}>{brokerSetup.description}</div>
                </div>
                <span
                  style={{
                    backgroundColor: "#e0e7ff",
                    color: "#3730a3",
                    borderRadius: "999px",
                    padding: "6px 10px",
                    fontWeight: 600,
                    textTransform: "capitalize",
                    fontSize: "12px",
                  }}
                >
                  {brokerSetup.auth_mode.replace(/_/g, " ")}
                </span>
              </div>
            </div>
          )}

          {selectedBroker && brokerFields.length > 0 && (
            <div className="broker-fields">
              <div style={{ fontWeight: 700, marginBottom: "12px" }}>Step 2: Save Broker Details</div>
              <div style={{ color: "#6b7280", fontSize: "14px", marginBottom: "14px" }}>
                Save the broker credentials once. AlgoView will retain them securely until you explicitly change or remove them.
              </div>
              {brokerSetup?.requirement_note && (
                <div style={{ color: "#374151", fontSize: "13px", marginBottom: "14px", background: "#f8fafc", border: "1px solid #e5e7eb", borderRadius: "8px", padding: "10px 12px" }}>
                  {brokerSetup.requirement_note}
                </div>
              )}
              {brokerFields.map((field, index) => (
                <FormGroup key={index}>
                  <Label for={field.key}>{field.label}</Label>
                  <Input
                    type={field.type || "text"}
                    id={field.key}
                    name={field.key}
                    placeholder={field.configured && field.secret ? `Leave blank to keep saved ${field.label}` : `Enter ${field.label}`}
                    value={brokerInput[field.key] || ""}
                    className={formErrors[field.key] ? "is-invalid" : ""}
                    onChange={handleInputChange}
                    autoComplete="off"
                  />
                  {field.configured && (
                    <small style={{ color: "#6b7280", display: "block", marginTop: "6px" }}>
                      {field.secret
                        ? `${field.label} is already stored securely. Leave blank to keep it unchanged.`
                        : `${field.label}: ${field.display_value || field.value || "Saved"}`}
                    </small>
                  )}
                  {formErrors[field.key] && (
                    <div className="invalid-feedback">
                      {`${field.label} is required.`}
                    </div>
                  )}
                </FormGroup>
              ))}

              <div
                style={{
                  background: "#f8fafc",
                  border: "1px solid #e5e7eb",
                  borderRadius: "12px",
                  padding: "14px 16px",
                  marginTop: "16px",
                }}
              >
                <div style={{ fontWeight: 700, marginBottom: "8px" }}>Step 3: Login / Generate Tokens</div>
                <div style={{ color: "#6b7280", fontSize: "14px" }}>
                  First save the broker details above. After that, use the separate login button to start the broker session or token-generation flow.
                </div>
                {(brokerSetup?.connect_path || brokerSetup?.auth_mode === "direct_credentials") && (
                  <div style={{ marginTop: "10px", fontSize: "13px", color: areRequiredBrokerFieldsReady ? "#166534" : "#b45309" }}>
                    {normalizeBrokerName(selectedBroker) === "dhan"
                      ? "Dhan login needs App/API Key, Secret, and Client ID. If you saved an Access Token directly, no login redirect is required."
                      : areRequiredBrokerFieldsReady
                        ? "Required broker details are available. You can start broker login after saving."
                        : "Fill all required broker details before starting broker login."}
                  </div>
                )}
                <div style={{ marginTop: "10px", display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                  <span style={runtimeBadgeStyles}>
                    {isRuntimeActive ? "Active" : "Inactive"}
                  </span>
                  <span style={{ fontSize: "13px", color: "#6b7280" }}>
                    Session: {runtimeSessionStatus} | Token: {runtimeTokenStatus}
                  </span>
                </div>
              </div>
            </div>
          )}

        </ModalBody>
        <ModalFooter>
          <Button
            color="secondary"
            onClick={() => {
              setSetupStep("select");
              setBrokerSetup(null);
              setBrokerFields([]);
              setSelectedBroker("");
              setbrokerInput({});
              setTouchedBrokerFields({});
              setFormErrors({});
            }}
            disabled={isSubmitting}
          >
            Choose Broker
          </Button>
          <Button
            className="search-btn-clr"
            onClick={setupStep === "select" ? handleSaveSelectedBroker : handleUpdate}
            disabled={isSubmitting || !selectedBroker || (setupStep !== "select" && !hasBrokerDetailsToSave)}
          >
            {isSubmitting
              ? "Saving..."
              : setupStep === "select"
                ? "Save Broker Name API Details"
                : (brokerSetup?.save_action_label || "Save Broker Name API Details")}
          </Button>
          <Button
            color="danger"
            onClick={closeModal}
            style={{ marginLeft: "10px" }}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
        </ModalFooter>
      </Modal>
      <Modal isOpen={isExecutionModalOpen} toggle={closeExecutionModal} size="lg">
        <ModalHeader toggle={closeExecutionModal}>Execution IP</ModalHeader>
        <ModalBody>
          <div
            style={{
              background: executionNode?.is_verified_with_broker ? "#f0fdf4" : "#fffbeb",
              border: `1px solid ${executionNode?.is_verified_with_broker ? "#bbf7d0" : "#fde68a"}`,
              borderRadius: "12px",
              padding: "14px 16px",
              marginBottom: "16px",
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: "6px" }}>
              {executionNode ? "Assigned static execution IP" : "No static execution IP added"}
            </div>
            <div style={{ color: "#4b5563", fontSize: "14px" }}>
              {executionNode
                ? `Broker verification: ${executionNode.is_verified_with_broker ? "Verified" : "Pending admin verification"}${executionNode.execution_type === "proxy" ? ` | Proxy IP: ${executionNode.proxy_public_ip_verified ? "Verified" : "Not verified"}` : ""}`
                : "Add the VPS/static IP that should place broker orders for your account."}
            </div>
          </div>

          <FormGroup>
            <Label>Execution Type</Label>
            <Input
              type="select"
              name="execution_type"
              value={executionNodeInput.execution_type}
              onChange={handleExecutionInputChange}
            >
              <option value="vps_node">VPS Node</option>
              <option value="proxy">Proxy IP</option>
            </Input>
          </FormGroup>
          <div className="row">
            <div className="col-md-6">
              <FormGroup>
                <Label>Node Name *</Label>
                <Input
                  name="name"
                  value={executionNodeInput.name}
                  onChange={handleExecutionInputChange}
                  placeholder="My execution VPS"
                />
              </FormGroup>
            </div>
            <div className="col-md-6">
              <FormGroup>
                <Label>Static IP *</Label>
                <Input
                  name="ip_address"
                  value={executionNodeInput.ip_address}
                  onChange={handleExecutionInputChange}
                  placeholder="3.109.40.137"
                />
              </FormGroup>
            </div>
          </div>
          <FormGroup>
            <Label>Provider</Label>
            <Input
              name="provider"
              value={executionNodeInput.provider}
              onChange={handleExecutionInputChange}
              placeholder={executionNodeInput.execution_type === "proxy" ? "Proxy vendor" : "AWS"}
            />
          </FormGroup>
          {executionNodeInput.execution_type === "vps_node" ? (
            <>
              <div className="row">
                <div className="col-md-6">
                  <FormGroup>
                    <Label>Node ID *</Label>
                    <Input
                      name="node_id"
                      value={executionNodeInput.node_id}
                      onChange={handleExecutionInputChange}
                      placeholder="my-node-1"
                    />
                  </FormGroup>
                </div>
                <div className="col-md-6">
                  <FormGroup>
                    <Label>Server URL *</Label>
                    <Input
                      name="server_url"
                      value={executionNodeInput.server_url}
                      onChange={handleExecutionInputChange}
                      placeholder="https://node1.example.com"
                    />
                  </FormGroup>
                </div>
              </div>
              <FormGroup>
                <Label>{executionNode ? "New Node Secret" : "Node Secret *"}</Label>
                <Input
                  type="password"
                  name="node_secret"
                  value={executionNodeInput.node_secret}
                  onChange={handleExecutionInputChange}
                  placeholder={executionNode ? "Leave blank to keep existing secret" : "Shared HMAC secret"}
                  autoComplete="off"
                />
              </FormGroup>
            </>
          ) : (
            <>
              <div className="row">
                <div className="col-md-4">
                  <FormGroup>
                    <Label>Proxy Protocol *</Label>
                    <Input type="select" name="proxy_protocol" value={executionNodeInput.proxy_protocol} onChange={handleExecutionInputChange}>
                      <option value="http">HTTP</option>
                      <option value="https">HTTPS</option>
                      <option value="socks5">SOCKS5</option>
                    </Input>
                  </FormGroup>
                </div>
                <div className="col-md-5">
                  <FormGroup>
                    <Label>Proxy Host / Hostname *</Label>
                    <Input name="proxy_host" value={executionNodeInput.proxy_host} onChange={handleExecutionInputChange} placeholder="proxy.vendor.com" />
                  </FormGroup>
                </div>
                <div className="col-md-3">
                  <FormGroup>
                    <Label>Proxy Port *</Label>
                    <Input name="proxy_port" value={executionNodeInput.proxy_port} onChange={handleExecutionInputChange} placeholder="8080" />
                  </FormGroup>
                </div>
              </div>
              <div className="row">
                <div className="col-md-6">
                  <FormGroup>
                    <Label>Proxy Username</Label>
                    <Input name="proxy_username" value={executionNodeInput.proxy_username} onChange={handleExecutionInputChange} autoComplete="off" />
                  </FormGroup>
                </div>
                <div className="col-md-6">
                  <FormGroup>
                    <Label>{executionNode ? "New Proxy Password" : "Proxy Password"}</Label>
                    <Input type="password" name="proxy_password" value={executionNodeInput.proxy_password} onChange={handleExecutionInputChange} placeholder={executionNode ? "Leave blank to keep existing password" : "Optional"} autoComplete="off" />
                  </FormGroup>
                </div>
              </div>
            </>
          )}
          <FormGroup check>
            <Input
              type="checkbox"
              name="is_active"
              checked={executionNodeInput.is_active}
              onChange={handleExecutionInputChange}
            />
            <Label check>Keep this execution IP active</Label>
          </FormGroup>
        </ModalBody>
        <ModalFooter>
          {executionNode && (
            <Button color="danger" outline onClick={handleReleaseExecutionNode} disabled={isExecutionSaving}>
              Release IP
            </Button>
          )}
          {executionNode?.execution_type === "proxy" && (
            <Button color="info" outline onClick={handleVerifyExecutionProxy} disabled={isExecutionSaving}>
              Verify Proxy IP
            </Button>
          )}
          <Button color="secondary" outline onClick={closeExecutionModal} disabled={isExecutionSaving}>
            Close
          </Button>
          <Button className="search-btn-clr" onClick={handleSaveExecutionNode} disabled={isExecutionSaving}>
            {isExecutionSaving ? "Saving..." : "Save Execution IP"}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default ClientHeader;
