import React, { useState, useEffect, useRef } from 'react';
import { Card, CardBody, Col, Label, Row, Form, FormGroup, Input, TabContent, TabPane, Nav, NavItem, NavLink, Table } from 'reactstrap';
import classnames from 'classnames';
import './Widgets1.css';
import { getOptionChainSocketUrl } from '../../../ConfigUrl/config';
import { getClientSegmentsList, getExpiryDate } from '../../../Services/Authentication';

const Widgets1 = ({ userProfile }) => {
  const isClient = userProfile?.role?.name === 'client';
  const [activeTab, setActiveTab] = useState('1');
  const [socketData, setSocketData] = useState([]);
  const [symbols, setSymbols] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [expiryDates, setExpiryDates] = useState([]);
  const [selectedExpiryDate, setSelectedExpiryDate] = useState('');
  const socketRef = useRef(null);

  // Function to toggle Tabs
  const toggleTab = (tab) => {
    if (activeTab !== tab) {
      setActiveTab(tab);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      await fetchClientSegments();
    };
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      const fetchExpiry = async () => {
        const response = await fetchExpiryDates(selectedSymbol);
        if (response?.expiry_dates?.length) {
          setSelectedExpiryDate(response.expiry_dates[0]);
        }
      };
      fetchExpiry();
    }
  }, [selectedSymbol]);

  useEffect(() => {
    if (selectedSymbol && selectedExpiryDate) {
      console.log('Selected Symbol:', selectedSymbol, 'Selected Expiry Date:', selectedExpiryDate);

      const socketUrl = getOptionChainSocketUrl(selectedSymbol, selectedExpiryDate);
      console.log('WebSocket URL:', socketUrl);

      if (socketRef.current) {
        console.log("Closing previous WebSocket connection");
        socketRef.current.close();
      }

      socketRef.current = new WebSocket(socketUrl);

      socketRef.current.onopen = () => {
        console.log('WebSocket connected successfully to:', socketUrl);
      };

      socketRef.current.onmessage = (event) => {
        console.log('Option Chain WebSocket message received:', event.data);
        try {
          const parsedData = JSON.parse(event.data);
          setSocketData((prevData) => {
            const updatedData = [...prevData];
            const existingIndex = updatedData.findIndex(
              (item) =>
                item.strike_price === parsedData.strike_price &&
                item.category === parsedData.category
            );

            if (existingIndex !== -1) {
              updatedData[existingIndex] = { ...updatedData[existingIndex], ...parsedData };
            } else {
              updatedData.push(parsedData);
            }

            return updatedData;
          });
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      socketRef.current.onclose = (event) => {
        console.error('WebSocket closed:', event.reason || 'No reason provided');
      };

      socketRef.current.onerror = (event) => {
        console.error('WebSocket error occurred:', event);
      };

      return () => {
        if (socketRef.current) {
          console.log('Cleaning up WebSocket connection.');
          socketRef.current.close();
        }
      };
    }
  }, [selectedSymbol, selectedExpiryDate]);


  const fetchClientSegments = async () => {
    try {
      const response = await getClientSegmentsList();
      const clientData = response?.client_segment_list || [];
      const uniqueSymbols = Array.from(new Set(clientData.map(item => item.symbol)));
      setSymbols(uniqueSymbols);
      // Set default values
      if (uniqueSymbols.length) setSelectedSymbol(uniqueSymbols[0]);
    } catch (err) {
      console.error('Error fetching client segments:', err);
    }
  };

  const fetchExpiryDates = async (symbol) => {
    try {
      const response = await getExpiryDate(symbol);
      setExpiryDates(response?.expiry_dates || []);
      if (response?.expiry_dates?.length) setSelectedExpiryDate(response.expiry_dates[0]);
    } catch (err) {
      console.error('Error fetching expiry dates:', err);
    }
  };

  const handleSymbolChange = (e) => {
    setSelectedSymbol(e.target.value);
  };

  const handleExpiryDateChange = (e) => {
    setSelectedExpiryDate(e.target.value);
  };

  // Group data by CE and PE
  const groupedData = socketData.reduce(
    (acc, data) => {
      if (data.category === 'CE') acc.CE.push(data);
      if (data.category === 'PE') acc.PE.push(data);
      return acc;
    },
    { CE: [], PE: [] }
  );

  // Render null if user is not a client
  if (!isClient) {
    return null;
  }

  return (
    <Col xxl="auto" xl="3" sm="6" className="box-col-6 custom-style" style={{ width: '100%', marginTop: '20px' }}>
      <Card>
        <CardBody>
          {/* Top Select Inputs */}
          <Form >
            <Row form>
              <Col md={3}>
                <FormGroup>
                  <Label for="symbols">Symbols</Label>
                  <Input
                    type="select"
                    className="w-auto custom-responsive"
                    style={{ color: 'black' }}
                    value={selectedSymbol}
                    onChange={handleSymbolChange}
                  >
                    {symbols.length === 0 ? (
                      <option value="">---</option>
                    ) : (
                      symbols.map((symbol, index) => (
                        <option key={index} value={symbol}>
                          {symbol}
                        </option>
                      ))
                    )}
                  </Input>
                </FormGroup>
              </Col>
              <Col md={3}>
                <FormGroup>
                  <Label for="expiryDate">Expiry Date</Label>
                  <Input
                    type="select"
                    className="w-auto custom-design"
                    value={selectedExpiryDate}
                    onChange={handleExpiryDateChange}
                  >
                    {expiryDates.length === 0 ? (
                      <option value="">---</option>
                    ) : (
                      expiryDates.map((date, index) => (
                        <option key={index} value={date}>
                          {date}
                        </option>
                      ))
                    )}
                  </Input>
                </FormGroup>
              </Col>
            </Row>
          </Form>
          {/* Tabs Section */}
          <Nav tabs>
            <NavItem>
              <NavLink
                className={classnames({ active: activeTab === '1' })}
                onClick={() => toggleTab('1')}
                style={{ cursor: 'pointer' }}
              >
                Option List
              </NavLink>
            </NavItem>
          </Nav>

          {/* Content under Tabs */}
          <TabContent activeTab={activeTab} className="mt-3">
            <TabPane tabId="1">
              <div>
                {/* Labels for CE and PE */}
                <div className="d-flex ">
                  <h5 style={{ marginLeft: '20%' }}>CE </h5>
                  <h5 style={{ marginLeft: '50%' }}>PE </h5>
                </div>

                {/* Options Table */}
                <div className="table-responsive table-container"
                  style={{
                    maxHeight: '400px',
                    overflowY: 'auto',
                  }}
                >
                  <Table bordered>
                    <thead>
                      <tr>
                        <th className='custom-col-design'>Volume</th>
                        <th className='custom-col-design'>LTP</th>
                        <th className='custom-col-design'>Strike Price</th>
                        <th className='custom-col-design'>LTP</th>
                        <th className='custom-col-design'>Volume</th>
                      </tr>
                    </thead>
                    <tbody>
                      {groupedData.CE.sort((a, b) => a.strike_price - b.strike_price).map((ceData, index) => {
                        const peData = groupedData.PE.find((item) => item.strike_price === ceData.strike_price);

                        // Utility function to style LTP based on formatted_percentage
                        const getLtpStyle = (formattedPercentage) => {
                          if (!formattedPercentage) return {};
                          if (formattedPercentage.includes("+")) return { color: "green" };
                          if (formattedPercentage.includes("-")) return { color: "red" };
                          return {};
                        };

                        // Function to truncate decimals
                        const truncateDecimal = (value) => {
                          return value ? Math.trunc(value) : '-';
                        };

                        return (
                          <tr key={index}>
                            {/* CE Data */}
                            <td>{ceData.volume || '-'}</td>
                            <td>
                              <div>
                                <span style={getLtpStyle(ceData.formatted_percentage)}>{ceData.ltp || '-'}</span>
                                <br />
                                <span style={{ color: "black", fontSize: "small" }}>
                                  {ceData.formatted_percentage || ''}
                                </span>
                              </div>
                            </td>
                            <td>{truncateDecimal(ceData.strike_price) || '-'}</td>

                            {/* PE Data */}
                            {peData ? (
                              <>
                                <td>
                                  <div>
                                    <span style={getLtpStyle(peData.formatted_percentage)}>{peData.ltp || '-'}</span>
                                    <br />
                                    <span style={{ color: "black", fontSize: "small" }}>
                                      {peData.formatted_percentage || '-'}
                                    </span>
                                  </div>
                                </td>
                                <td>{peData.volume || '-'}</td>
                              </>
                            ) : (
                              <td colSpan="3" style={{ textAlign: 'center' }}>No PE Data</td>
                            )}
                          </tr>
                        );
                      })}
                    </tbody>
                  </Table>
                </div>

              </div>
            </TabPane>
          </TabContent>
        </CardBody>
      </Card>
    </Col>
  );
};

export default Widgets1;
