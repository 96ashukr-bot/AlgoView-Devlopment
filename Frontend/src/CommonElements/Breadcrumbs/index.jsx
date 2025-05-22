import React, { Fragment, useContext, useState, useEffect } from 'react';
import { Container, Row, Col, FormGroup, Input } from 'reactstrap';
import { Link, useLocation } from 'react-router-dom';
import H3 from '../Headings/H3Element';
import CustomizerContext from '../../_helper/Customizer';
import Swal from 'sweetalert2';
import SvgIcon from '../../Components/Common/Component/SvgIcon';
import { fetchUserProfile, BrokerAuthLogin, getClientBrokerDetail, getBrokerTokenExpiry } from '../../Services/Authentication';

const Breadcrumbs = (props) => {
  const { layoutURL } = useContext(CustomizerContext);
  const [role, setRole] = useState('');
  const [brokerName, setBrokerName] = useState('');
  const [isToggleOn, setIsToggleOn] = useState(false);
  const location = useLocation();

  useEffect(() => {
    loadUserRole();
    loadBrokerDetails();
    checkBrokerTokenStatus();
  }, []);

  const loadUserRole = async () => {
    try {
      const data = await fetchUserProfile();
      if (data && data.role && data.role.name) {
        setRole(data.role.name.toLowerCase());
      }
    } catch (error) {
      console.error('Error fetching user role:', error);
    }
  };

  // URL based on role
  const getDashboardURL = () => {
    if (role === 'client') {
      return `/dashboard/algoviewtech/user`;
    } else if (role === "Super-Admin") {
      return `/dashboard/algoviewtech/admin`;
    } else if (role === "Sub-Admin") {
      return `/dashboard/algoviewtech/admin`;
    }
    return '/dashboard/algoviewtech/admin';
  };

  const loadBrokerDetails = async () => {
    try {
      const response = await getClientBrokerDetail();
      if (response?.data?.broker_name?.broker_name) {
        setBrokerName(response.data.broker_name.broker_name.toLowerCase());
      }
    } catch (error) {
      console.error('Error fetching broker details:', error);
    }
  };

  const checkBrokerTokenStatus = async () => {
    try {
      const response = await getBrokerTokenExpiry();
      if (response && typeof response.isTokenExpired !== 'undefined') {
        setIsToggleOn(!response.isTokenExpired);
      }
    } catch (error) {
      console.error('Error fetching broker token status:', error);
    }
  };

  const handleToggle = () => {
    const newState = !isToggleOn;
    setIsToggleOn(newState);

    if (newState) {
      BrokerAuthLogin()
        .then((response) => {
          window.location.href = response.redirect_url;
        })
        .catch((error) => {
          const errorMessage = error?.error || 'Something went wrong. Please try again.';

          Swal.fire({
            icon: 'error',
            title: 'Authentication Failed',
            text: `Error: ${errorMessage}`,
            confirmButtonText: 'OK'
          });
          setIsToggleOn(false);
        });
    }
  };

  return (
    <Fragment>
      <Container fluid={true}>
        <div className='page-title'>
          <Row>
            <Col xs='6'>
              <H3>Dashboard</H3>
            </Col>
            <Col xs='6'>
              <ol className='breadcrumb'>
                {(location.pathname === '/dashboard/algoviewtech/user' && ['zerodha', 'upstox', '5paisa', 'fyers'].includes(brokerName.toLowerCase())) && (
                  <>
                    <h4 style={{ marginBottom: '0px' }}>
                      {isToggleOn ? 'Broker Logged' : 'Broker Login'}
                    </h4>
                    <FormGroup switch className="switch-toggle-custom" style={{ paddingRight: '1rem' }}>
                      <Input
                        style={{ width: '50px', height: '25px', border: '1px solid gray' }}
                        type="checkbox"
                        name="switchOption"
                        id="switchOption"
                        checked={isToggleOn}
                        onChange={handleToggle}
                      />
                    </FormGroup>
                  </>
                )}

                <li className='breadcrumb-item'>
                  <Link to={getDashboardURL()}>
                    <SvgIcon iconId='stroke-home' />
                  </Link>
                </li>
                <li className='breadcrumb-item'>{props.parent}</li>
                {props.subParent ? <li className='breadcrumb-item'>{props.subParent}</li> : ''}
                <li className='breadcrumb-item active'>{props.title}</li>
              </ol>
            </Col>
          </Row>
        </div>
      </Container>
    </Fragment>
  );
};

export default Breadcrumbs;
