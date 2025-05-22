import React, { useState, useEffect } from 'react';
import {
  Card, CardBody, Input, Button, Col, Nav, NavItem, NavLink, TabContent, TabPane,
} from 'reactstrap';
import classnames from 'classnames';
import { getWebSocketUrl } from '../../../ConfigUrl/config';
import { useNavigate } from 'react-router-dom';
import {
  FaExchangeAlt, FaEdit, FaTrash, FaLink, FaSignInAlt, FaChartLine, FaToggleOn, FaToggleOff, FaArrowDown, FaArrowUp
} from 'react-icons/fa';
import { getClientSegmentsList, updateTradeStatus } from '../../../Services/Authentication';
import useWebSocket from 'react-use-websocket';
import './Dashboards.css';

const GreetingCard = ({ userProfile }) => {
  const isClient = userProfile?.role?.name === 'client';
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('1');
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [clientSegments, setClientSegments] = useState([]);
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
  }, []);

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
      const response = await getClientSegmentsList();
      console.log('Fetched client segments:', response);
      setClientSegments(response?.client_segment_list || []);
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
    const payload = {
      segment: segment.segment.id,
      sub_segment: segment.sub_segment.id,
      is_trade_status: !segment.is_tread_status,
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
    const clientId = segment?.client;
    const segmentId = segment?.segment?.id;
    const subSegmentId = segment?.sub_segment?.id;

    if (!clientId || !segmentId || !subSegmentId) {
      console.error('Missing required segment data:', { clientId, segmentId, subSegmentId });
      return;
    }

    navigate(`/dashboard/segments/update-segment/${clientId}/${segmentId}/${subSegmentId}`);
  };

  if (!isClient) {
    return null;
  }

  return (
    <Col className="col-xxl-4 col-sm-6 box-col-6 mt-4">
      <Card className='bg-white dark'>
        <CardBody>
          <Nav tabs>
            <NavItem>
              <NavLink
                className={classnames({ active: activeTab === '1' })}
                onClick={() => toggle('1')}
              >
                OPTIONS
              </NavLink>
            </NavItem>
          </Nav>

          <TabContent activeTab={activeTab} className="mt-3">
            <TabPane tabId="1">
              {loading ? (
                <div>Loading...</div>
              ) : clientSegments.length > 0 ? (
                clientSegments.map((segment, index) => (
                  <div
                    key={index}
                    className="d-flex justify-content-between align-items-center py-4 position-relative"
                    style={{
                      borderBottom:
                        index !== clientSegments.length - 1
                          ? '1px solid #eee'
                          : 'none',
                      fontSize: '14px',
                    }}
                    onMouseEnter={() => setHoveredIndex(index)}
                    onMouseLeave={() => setHoveredIndex(null)}
                  >
                    <div>
                      <span>{segment?.sub_segment?.name || 'Unnamed Sub-segment'}</span>
                    </div>
                    <div className="d-flex align-items-center">
                      {/* Price : */}
                      <span className="ms-3">
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
                      {/* Display the Difference and Percentage */}
                      <div className="ms-3">
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
                      <div
                        className="hover-options d-flex position-absolute hover-stripe"
                        style={{
                          background: '#f8f9fa',
                          padding: '10px',
                          paddingBottom: '5px',
                          paddingTop: '5px',
                          border: '1px solid #ccc',
                          borderRadius: '8px',
                          top: '50%',
                          paddingTop: '12px',
                          paddingBottom: '3px',
                          transform: 'translateY(-50%)',
                          boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
                        }}
                      >
                        <Button
                          style={{ padding: '0 18px', fontSize: '35px' }}
                          color="link"
                          title="Toggle On/Off"
                          onClick={() => handleToggle(segment)}
                        >
                          {segment.is_tread_status ? (
                            <FaToggleOn color="primary" />
                          ) : (
                            <FaToggleOff color="gray" />
                          )}
                        </Button>
                        <Button
                          color="link"
                          title="Edit"
                          style={{ padding: '0 18px', fontSize: '25px' }}
                          onClick={() => handleEdit(segment)}
                        >
                          <FaEdit />
                        </Button>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div>No segments found.</div>
              )}
            </TabPane>
          </TabContent>
        </CardBody>
      </Card>
    </Col>
  );
};

export default GreetingCard;
