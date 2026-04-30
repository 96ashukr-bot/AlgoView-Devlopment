import React, { Fragment, useContext, useState, useEffect } from 'react';
import { Container, Row, Col } from 'reactstrap';
import { Link, useLocation } from 'react-router-dom';
import H3 from '../Headings/H3Element';
import CustomizerContext from '../../_helper/Customizer';
import SvgIcon from '../../Components/Common/Component/SvgIcon';
import { fetchUserProfile } from '../../Services/Authentication';

const Breadcrumbs = (props) => {
  useContext(CustomizerContext);
  const [role, setRole] = useState('');
  useLocation();

  useEffect(() => {
    loadUserRole();
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
