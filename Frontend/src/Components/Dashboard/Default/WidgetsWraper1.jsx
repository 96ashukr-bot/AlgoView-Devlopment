import React, { useEffect, useState } from 'react';
import { Col, Row } from 'reactstrap';
import SuperWidgets from '../../Common/CommonWidgets/SuperWidgets';
import { getSubAdmins, getInactiveClient, getActiveClient } from '../../../Services/Authentication';
import { getWidgetsData } from '../../../Data/DefaultDashboard'; 

const WidgetsWrapper1 = () => {
  const [subAdminsData, setSubAdminsData] = useState(null);
  const [inactiveClientData, setInactiveClientData] = useState(null);
  const [activeClientData, setActiveClientData] = useState(null);
  const [widgetsData, setWidgetsData] = useState([]);

  const userProfile = {
    role: {
      name: "client", 
    },
  };

  const isClient = userProfile?.role?.name === "client";

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const subAdmins = await getSubAdmins();
      console.log('Sub Admins:', subAdmins);
      
      const inactiveClients = await getInactiveClient();
      console.log('Inactive Clients:', inactiveClients);
  
      const activeClients = await getActiveClient();
      console.log('Active Clients:', activeClients);
  
      setSubAdminsData(subAdmins);
      setInactiveClientData(inactiveClients);
      setActiveClientData(activeClients);
  
      setWidgetsData(getWidgetsData(subAdmins, inactiveClients, activeClients));
    } catch (error) {
      console.error('Error fetching widget data:', error);
    }
  };

  return (
    <>
      {isClient &&
        widgetsData.map((data, index) => (
          <Col key={index} xxl='auto' xl='3' sm='6' className='box-col-6'>
            <Row>
              <Col xl='12'>
                <SuperWidgets data={data} />
              </Col>
            </Row>
          </Col>
        ))}
    </>
  );
};

export default WidgetsWrapper1;