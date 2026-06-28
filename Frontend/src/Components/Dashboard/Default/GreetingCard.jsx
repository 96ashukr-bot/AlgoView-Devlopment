import React, { useState, useEffect } from 'react';
import {
  Card, CardBody, Button, Col, Nav, NavItem, NavLink, TabContent, TabPane,
} from 'reactstrap';
import classnames from 'classnames';
import { getWebSocketUrl } from '../../../ConfigUrl/config';
import { useNavigate } from 'react-router-dom';
import {
  FaEdit, FaToggleOn, FaToggleOff, FaArrowDown, FaArrowUp, FaLock
} from 'react-icons/fa';
import { getClientSegmentsList, getClientMultiLegSettings, updateTradeStatus, updateClientMultiLegTradeStatus } from '../../../Services/Authentication';
import useWebSocket from 'react-use-websocket';
import './Dashboards.css';
import Swal from 'sweetalert2';

const GreetingCard = ({ userProfile, clientId = "" }) => {
  const roleName = String(userProfile?.role?.name || '').trim().toLowerCase();
  const canViewClientScripts = ['client', 'user'].includes(roleName) || Boolean(clientId);
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('1');
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [clientSegments, setClientSegments] = useState([]);
  const [multiLegStrategies, setMultiLegStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tokenPrices, setTokenPrices] = useState({});
  const [priceChanges, setPriceChanges] = useState({});
  const [webSocketUrl, setWebSocketUrl] = useState('');

  const { sendMessage, lastMessage } = useWebSocket(webSocketUrl || null, {
    shouldReconnect: () => !!webSocketUrl, // Only reconnect if the URL is valid
    onError: (error) => console.error("WebSocket error:", error),
    onOpen: () => console.log('Card WebSocket connected'),
    onClose: () => console.log('Card WebSocket disconnected'),
  });

  useEffect(() => {
    fetchData();
  }, [clientId]);

  useEffect(() => {
    if (lastMessage !== null) {
      const messageData = JSON.parse(lastMessage.data);
      console.log('Received WebSocket card message :', messageData);

      // Update price and change for the specific token
      if (messageData.token && messageData.price) {
        setTokenPrices((prevPrices) => ({
          ...prevPrices,
          [messageData.token]: parseFloat(messageData.price.replace(/,/g, '')), // Remove commas for parsing
        }));

        // Include `trend`, `difference`, and `percentage`
        if (messageData.trend && messageData.difference && messageData.percentage) {
          setPriceChanges((prevChanges) => ({
            ...prevChanges,
            [messageData.token]: {
              trend: messageData.trend,
              difference: messageData.difference,
              percentage: messageData.percentage,
            },
          }));
        }
      }

    }
  }, [lastMessage]);

  const fetchData = async () => {
    try {
      const [response, multiLegResponse] = await Promise.all([
        getClientSegmentsList(clientId ? { client: clientId } : {}),
        getClientMultiLegSettings({ include_locked: true, ...(clientId ? { client: clientId } : {}) }),
      ]);
      console.log('Fetched client segments:', response);
      setClientSegments(response?.client_segment_list || []);
      setMultiLegStrategies(Array.isArray(multiLegResponse) ? multiLegResponse : []);
      setLoading(false);

      // const Exchange = response.client_segment_list[0]?.sub_segment?.Exchange;
      // const tokens = response.client_segment_list.map(segment => segment.sub_segment.token);

      // if (tokens.length > 0) {
      //   const socketUrl = getWebSocketUrl(Exchange, tokens.join(','));
      //   console.log('WebSocket URL Chrome/FireFox:', socketUrl);
      //   setWebSocketUrl(socketUrl);
      // }

      const Exchange = response.client_segment_list[0]?.sub_segment?.Exchange;
      const tokens = response.client_segment_list
        .map(segment => segment.sub_segment?.token)
        .filter(token => token); // Remove falsy values (null, undefined, empty string)

      if (Exchange && tokens.length > 0) { // Ensure Exchange & tokens exist before constructing the WebSocket URL
        const socketUrl = getWebSocketUrl(Exchange, tokens.join(','));
        console.log('WebSocket URL Chrome/FireFox:', socketUrl);
        setWebSocketUrl(socketUrl);
      } else {
        console.warn('Exchange or tokens not found, WebSocket connection not established.');
      }
      
    } catch (error) {
      console.error('Error fetching client segments:', error);
      setLoading(false);
    }
  };

  const toggle = (tab) => {
    if (activeTab !== tab) setActiveTab(tab);
  };

  const handleToggle = async (segment) => {
    if (segment?.is_locked) {
      Swal.fire("Locked", "This script is not included in your assigned group service.", "info");
      return;
    }

    const payload = {
      segment: segment.segment.id,
      sub_segment: segment.sub_segment.id,
      is_trade_status: !segment.is_tread_status,
      ...(clientId ? { client: clientId } : {}),
    };

    try {
      const response = await updateTradeStatus(payload);
      console.log('API Response:', response);

      // Update the UI with the new status
      setClientSegments((prev) =>
        prev.map((item) =>
          item.sub_segment.id === segment.sub_segment.id
            ? { ...item, is_tread_status: payload.is_trade_status }
            : item
        )
      );

      // Optionally send a message via WebSocket
      sendMessage(JSON.stringify({ type: 'UPDATE_STATUS', payload }));
    } catch (error) {
      console.error('Error updating trade status:', error);
    }
  };

  const handleEdit = (segment) => {
    if (segment?.is_locked) {
      Swal.fire("Locked", "This script is not included in your assigned group service.", "info");
      return;
    }

    const targetClientId = segment?.client || clientId;
    const segmentId = segment?.segment?.id;
    const subSegmentId = segment?.sub_segment?.id;

    if (!targetClientId || !segmentId || !subSegmentId) {
      console.error('Missing required segment data:', { clientId: targetClientId, segmentId, subSegmentId });
      return;
    }

    navigate(`/dashboard/segments/update-segment/${targetClientId}/${segmentId}/${subSegmentId}`);
  };

  const handleMultiLegEdit = (strategy) => {
    if (strategy?.is_locked) {
      Swal.fire("Locked", "This multi leg strategy is locked. Please contact admin to enable it.", "info");
      return;
    }
    if (!strategy?.strategy) {
      return;
    }
    navigate(`/dashboard/strategies/update-multi-leg/${strategy.strategy}`);
  };

  const handleMultiLegToggle = async (strategy) => {
    if (strategy?.is_locked) {
      Swal.fire("Locked", "This multi leg strategy is locked. Please contact admin to enable it.", "info");
      return;
    }
    const payload = {
      strategy: strategy.strategy,
      is_trade_status: !strategy.is_tread_status,
      ...(clientId ? { client: clientId } : {}),
    };

    try {
      await updateClientMultiLegTradeStatus(payload);
      setMultiLegStrategies((prev) =>
        prev.map((item) =>
          item.strategy === strategy.strategy
            ? { ...item, is_tread_status: payload.is_trade_status }
            : item
        )
      );
    } catch (error) {
      console.error('Error updating multi leg trade status:', error);
    }
  };

  if (!canViewClientScripts) {
    return null;
  }

  const getDisplayScriptName = (segment) => {
    return segment?.script_name || segment?.sub_segment?.name || 'Unassigned Script';
  };

  return (
    <Col className="col-xxl-12 col-sm-12 box-col-12 mt-4 client-strategy-section">
      <Card className='bg-white dark client-strategy-card'>
        <CardBody>
          <Nav tabs className="client-dashboard-tabs justify-content-center">
            <NavItem>
              <NavLink
                className={classnames({ active: activeTab === '1' })}
                onClick={() => toggle('1')}
              >
                OPTIONS
              </NavLink>
            </NavItem>
            <NavItem>
              <NavLink
                className={classnames({ active: activeTab === '2' })}
                onClick={() => toggle('2')}
              >
                MULTI LEG
              </NavLink>
            </NavItem>
          </Nav>

          <TabContent activeTab={activeTab} className="mt-3">
            <TabPane tabId="1">
              {loading ? (
                <div>Loading...</div>
              ) : clientSegments.length > 0 ? (
                <div className="client-script-grid">
                  {clientSegments.map((segment, index) => (
                    <div
                      key={index}
                      className={`client-script-card position-relative ${segment?.is_locked ? 'client-script-card-locked' : ''}`}
                      onMouseEnter={() => setHoveredIndex(index)}
                      onMouseLeave={() => setHoveredIndex(null)}
                    >
                      <div
                        onClick={() => handleEdit(segment)}
                        style={{ cursor: 'pointer' }}
                        title="Edit trade setting"
                      >
                        <div className="client-script-title">
                          {getDisplayScriptName(segment)}
                          {segment?.is_locked ? (
                            <span className="badge bg-secondary ms-2">
                              <FaLock size={10} className="me-1" />
                              Locked
                            </span>
                          ) : null}
                        </div>
                        <div className="client-script-meta">
                          Group Service: {segment?.group_service || 'Not Assigned'}
                        </div>
                        <div className="client-script-meta">
                          Segment: {segment?.segment?.name || 'Not Assigned'}
                        </div>
                      </div>
                      <div className="client-script-info">
                        <span>
                          {tokenPrices[segment?.sub_segment?.token] ? (
                            <span
                              style={{
                                color: priceChanges[segment.sub_segment.token]?.trend === '+' ? 'green' : 'red',
                                display: 'flex',
                                alignItems: 'center',
                              }}
                            >
                              {tokenPrices[segment.sub_segment.token].toFixed(2)}
                              {priceChanges[segment.sub_segment.token]?.trend === '+' ? (
                                <FaArrowUp className='arrows' style={{ color: 'green' }} />
                              ) : (
                                <FaArrowDown className='arrows' style={{ color: 'red' }} />
                              )}
                            </span>
                          ) : (
                            '00.0'
                          )}
                        </span>
                        <div className="client-script-limits">
                          {segment?.group_qty_limit ? (
                            <div>Max Qty: {segment.group_qty_limit}</div>
                          ) : null}
                          {segment?.group_lot_size ? (
                            <div>Lot Size: {segment.group_lot_size}</div>
                          ) : null}
                        </div>
                        <div className="client-script-change">
                          {priceChanges[segment.sub_segment.token] && (
                            <>
                              <span
                                style={{
                                  color: priceChanges[segment.sub_segment.token]?.difference.startsWith('+') ? 'green' : 'red',
                                }}
                              >
                                {priceChanges[segment.sub_segment.token]?.difference || '0.00'}
                              </span>
                              <span
                                style={{
                                  color: parseFloat(priceChanges[segment.sub_segment.token]?.percentage.replace(/[()%]/g, '')) > 0 ? 'green' : 'red',
                                  marginLeft: '5px',
                                }}
                              >
                                {priceChanges[segment.sub_segment.token]?.percentage || '(+0.00%)'}
                              </span>
                            </>
                          )}
                        </div>
                      </div>

                      {hoveredIndex === index && (
                        <div className="hover-options d-flex position-absolute hover-stripe client-script-actions">
                          <Button
                            style={{ padding: '0 12px', fontSize: '30px' }}
                            color="link"
                            title="Toggle On/Off"
                            onClick={() => handleToggle(segment)}
                          >
                            {segment?.is_locked ? (
                              <FaLock color="#adb5bd" />
                            ) : segment.is_tread_status ? (
                              <FaToggleOn color="primary" />
                            ) : (
                              <FaToggleOff color="gray" />
                            )}
                          </Button>
                          <Button
                            color="link"
                            title="Edit"
                            style={{ padding: '0 12px', fontSize: '22px' }}
                            onClick={() => handleEdit(segment)}
                          >
                            {segment?.is_locked ? <FaLock color="#adb5bd" /> : <FaEdit />}
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div>No allotted scripts found.</div>
              )}
            </TabPane>
            <TabPane tabId="2">
              {loading ? (
                <div>Loading...</div>
              ) : multiLegStrategies.length > 0 ? (
                <div className="client-script-grid">
                {multiLegStrategies.map((strategy, index) => (
                  <div
                    key={strategy.id}
                    className="client-script-card client-multileg-card position-relative"
                  >
                    <div
                      onClick={() => handleMultiLegEdit(strategy)}
                      style={{ cursor: 'pointer' }}
                      title="Edit multi leg strategy"
                    >
                      <div style={{ fontWeight: 700, color: '#1f2a44' }}>
                        {strategy.strategy_name}
                        {strategy.is_locked ? (
                          <span className="badge bg-secondary ms-2">
                            <FaLock size={10} className="me-1" />
                            Locked
                          </span>
                        ) : null}
                      </div>
                      <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '4px' }}>
                        Template: {strategy.multi_leg_template_label || 'Multi Leg Strategy'}
                      </div>
                      <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '2px' }}>
                        Group Service: {strategy.group_service || 'Not Assigned'}
                      </div>
                      <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '2px' }}>
                        Segment: {strategy?.segment?.name || 'Not Assigned'}
                      </div>
                    </div>
                    <div className="d-flex align-items-center">
                      <div className="ms-3 text-end">
                        {strategy?.quantity ? (
                          <div style={{ fontSize: '12px', color: '#6c757d' }}>
                            Qty: {strategy.quantity}
                          </div>
                        ) : null}
                        {strategy?.expiry_date ? (
                          <div style={{ fontSize: '12px', color: '#6c757d' }}>
                            Expiry: {new Date(strategy.expiry_date).toLocaleDateString('en-IN')}
                          </div>
                        ) : null}
                      </div>
                      <div className="ms-4 d-flex align-items-center">
                        <Button
                          color="link"
                          className="p-0 me-3"
                          onClick={() => handleMultiLegToggle(strategy)}
                          title={strategy.is_locked ? 'Locked strategy' : (strategy.is_tread_status ? 'Disable strategy' : 'Enable strategy')}
                        >
                          {strategy.is_locked ? (
                            <FaLock size={20} color="#adb5bd" />
                          ) : strategy.is_tread_status ? (
                            <FaToggleOn size={24} color="#28a745" />
                          ) : (
                            <FaToggleOff size={24} color="#adb5bd" />
                          )}
                        </Button>
                        <Button
                          color="link"
                          className="p-0"
                          onClick={() => handleMultiLegEdit(strategy)}
                          title={strategy.is_locked ? 'Locked strategy' : 'Edit strategy'}
                        >
                          {strategy.is_locked ? <FaLock size={18} color="#adb5bd" /> : <FaEdit size={18} color="#283F7B" />}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
                </div>
              ) : (
                <div>No allotted multi leg strategies found.</div>
              )}
            </TabPane>
          </TabContent>
        </CardBody>
      </Card>
    </Col>
  );
};

export default GreetingCard;
