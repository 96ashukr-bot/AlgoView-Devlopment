import React, { useState } from "react";
import { Table, Card, CardBody, Input, Row, Col, Button, Nav, NavItem, NavLink } from "reactstrap";
import {
  FaExchangeAlt,
  FaEdit,
  FaTrash,
  FaLink,
  FaSignInAlt,
  FaChartLine,
  FaToggleOn,
  FaToggleOff,
} from 'react-icons/fa';
import classnames from "classnames";
import { useNavigate } from 'react-router-dom';


const Options = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("1");

  const toggle = (tab) => {
    if (activeTab !== tab) setActiveTab(tab);
  };

  const handleEdit = () => {
    navigate('/dashboard/segments/update-segment/:id'); // Redirect to EditPage
  };

  const handleChain = () => {
    navigate('/dashboard/optionchain/:id'); // Redirect to EditPage
  };
  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  const profitOrLoss = 200;

  // Dummy data
  const data = [
    { name: 'NIFTY 50', value: 23548.95, change: -10.1 },
    { name: 'NIFTY BANK', value: 50289.45, change: 0 },
    { name: 'NIFTY FIN SERVICE', value: 23243.35, change: 104.95 },
    { name: 'NIFTY MID SELECT', value: 12125.75, change: 54.65 },
  ];

  const getColor = (change) => {
    if (change > 0) return 'text-success';
    if (change < 0) return 'text-danger';
    return 'text-muted';
  };

  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [isToggled, setIsToggled] = useState(false); // Toggle state
  const buttonStyle = { width: '24px', height: '24px', fontSize: '18px' };

  const handleToggle = () => setIsToggled((prev) => !prev); // Toggle function


  return (
    <div style={{ padding: "20px" }}>
      <Row>
        {/* Left Sidebar: Watchlist */}
        <Col className="col-xxl-4 col-sm-6 box-col-6">
          <Card
            style={{
              backgroundColor: 'white',
              color: 'black',
            }}
          >
            <CardBody>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <Input
                  type="text"
                  placeholder="Search Product Name"
                  style={{
                    width: '65%',
                    border: '1px solid #ccc',
                    padding: '8px',
                    borderRadius: '5px',
                    color: 'black',
                  }}
                />
                <Button
                className="btn btn-primary search-btn-clr"
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#007bff',
                    border: 'none',
                    borderRadius: '5px',
                  }}
                >
                  + Add Watch
                </Button>
              </div>
              {data.map((item, index) => (
                <div
                  key={index}
                  className="d-flex justify-content-between align-items-center py-4 position-relative"
                  style={{
                    borderBottom: index !== data.length - 1 ? '1px solid #eee' : 'none',
                    fontSize: '14px',
                  }}
                  onMouseEnter={() => setHoveredIndex(index)}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
                  <div>
                    <span>{item.name}</span>
                  </div>
                  <div className="d-flex align-items-center">
                    <span
                      className={`me-2 ${getColor(item.change)}`}
                      style={{ fontWeight: 'bold', fontSize: '16px' }}
                    >
                      {item.value.toLocaleString()}
                    </span>
                    <span className={`${getColor(item.change)}`}>
                      {item.change > 0 ? `+${item.change}` : item.change}
                    </span>
                  </div>
                  {hoveredIndex === index && (
                    <div
                      className="hover-options d-flex position-absolute"
                      style={{
                        background: '#f8f9fa',
                        padding: '10px',
                        paddingBottom: '20px',
                        border: '1px solid #ccc',
                        borderRadius: '8px',
                        top: '50%',
                        right: '-36px',
                        transform: 'translateY(-50%)',
                        boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
                      }}
                    >
                      <Button color="link" title="Buy/Sell" style={buttonStyle}>
                        <FaExchangeAlt />
                      </Button>
                      <Button color="link" title="Toggle On/Off" onClick={handleToggle} style={buttonStyle}>
                        {isToggled ? <FaToggleOn color="primary" /> : <FaToggleOff color="gray" />}
                      </Button>
                      <Button color="link" title="Edit" style={buttonStyle} onClick={handleEdit}>
                        <FaEdit />
                      </Button>
                      <Button color="link" title="Remove" style={buttonStyle}>
                        <FaTrash />
                      </Button>
                      <Button color="link" title="Chain" style={buttonStyle} onClick={handleChain}>
                        <FaLink />
                      </Button>
                      <Button color="link" title="Login" style={buttonStyle}>
                        <FaSignInAlt />
                      </Button>
                      <Button color="link" title="Chart" style={buttonStyle}>
                        <FaChartLine />
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </CardBody>
          </Card>
        </Col>

        {/* Main Content: Option Chain */}
        <Col xxl='auto' xl='3' sm='6' className='box-col-6' style={{ width: '66.6%' }}>
          <Card>
            <CardBody>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <Input type="select" className="w-auto" style={{ width: '150px', color: "black" }}>
                  <option value="NIFTY 50">NIFTY 50</option>
                  <option value="NIFTY BANK">NIFTY BANK</option>
                  <option value="NIFTY FIN SERVICE">NIFTY FIN SERVICE</option>
                  <option value="NIFTY MID SELECT">NIFTY MID SELECT</option>
                </Input>
                {/* <span
                  style={{
                    color: profitOrLoss > 0 ? "green" : "red",
                    fontWeight: "bold",
                    marginLeft: "10px",
                  }}
                >
                  {profitOrLoss > 0 ? `+${profitOrLoss}` : profitOrLoss}
                </span> */}
                <Input type="select" className="w-auto">
                  <option value="14NOV24">14NOV24</option>
                </Input>
              </div>

              {/* Tabs Section */}
              <Nav tabs>
                <NavItem>
                  <NavLink
                    className={classnames({ active: activeTab === "1" })}
                    onClick={() => toggle("1")}
                    style={{ cursor: "pointer" }}
                  >
                    Option List
                  </NavLink>
                </NavItem>
                <NavItem>
                  <NavLink
                    className={classnames({ active: activeTab === "2" })}
                    onClick={() => toggle("2")}
                    style={{ cursor: "pointer" }}
                  >
                    Charts
                  </NavLink>
                </NavItem>
              </Nav>

              {/* Content under Tabs */}
              <div className="mt-3">
                {activeTab === "2" && <div>Charts will be displayed here.</div>}
                {activeTab === "1" && (
                  <div>
                    {/* Labels for CE and PE */}
                    <div className="d-flex">
                      <h5 style={{ marginLeft: '20%' }}>CE</h5>
                      <h5 style={{ marginLeft: '50%' }}>PE</h5>
                    </div>

                    {/* Options Table */}
                    <Table bordered>
                      <thead>
                        <tr>
                          <th>Product</th>
                          <th>Strike</th>
                          <th>Point</th>
                          <th>LTP</th>
                          <th>Product</th>
                          <th>Strike</th>
                          <th>Point</th>
                          <th>LTP</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>NIFTY24N1423100CE</td>
                          <td>23100</td>
                          <td>-26</td>
                          <td>439.15</td>
                          <td>NIFTY24N1423100PE</td>
                          <td>23100</td>
                          <td>-4</td>
                          <td>0.75</td>
                        </tr>
                        <tr>
                          <td>NIFTY24N1423150CE</td>
                          <td>23150</td>
                          <td>-17</td>
                          <td>393.15</td>
                          <td>NIFTY24N1423150PE</td>
                          <td>23150</td>
                          <td>-5</td>
                          <td>0.85</td>
                        </tr>
                        <tr>
                          <td>NIFTY24N1423100CE</td>
                          <td>23100</td>
                          <td>-26</td>
                          <td>439.15</td>
                          <td>NIFTY24N1423100PE</td>
                          <td>23100</td>
                          <td>-4</td>
                          <td>0.75</td>
                        </tr>
                        <tr>
                          <td>NIFTY24N1423150CE</td>
                          <td>23150</td>
                          <td>-17</td>
                          <td>393.15</td>
                          <td>NIFTY24N1423150PE</td>
                          <td>23150</td>
                          <td>-5</td>
                          <td>0.85</td>
                        </tr>
                        <tr>
                          <td>NIFTY24N1423100CE</td>
                          <td>23100</td>
                          <td>-26</td>
                          <td>439.15</td>
                          <td>NIFTY24N1423100PE</td>
                          <td>23100</td>
                          <td>-4</td>
                          <td>0.75</td>
                        </tr>
                        <tr>
                          <td>NIFTY24N1423150CE</td>
                          <td>23150</td>
                          <td>-17</td>
                          <td>393.15</td>
                          <td>NIFTY24N1423150PE</td>
                          <td>23150</td>
                          <td>-5</td>
                          <td>0.85</td>
                        </tr>
                        {/* Add more rows as needed */}
                      </tbody>
                    </Table>
                  </div>
                )}
              </div>
            </CardBody>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Options;
