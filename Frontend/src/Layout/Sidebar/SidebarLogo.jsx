import React, { useContext, useState } from 'react';
import { Grid } from 'react-feather';
import { Link } from 'react-router-dom';
import { Image } from '../../AbstractElements';
import CubaIcon from '../../assets/images/logo/logo (1).png';
import CustomizerContext from '../../_helper/Customizer';
import { fetchUserProfile } from '../../Services/Authentication';
import { useEffect } from 'react';
import './siderbarlogo.css';
import { LogoContext } from '../../Components/UiKits/Logo/LogoContext';

const SidebarLogo = () => {
  const { logo } = useContext(LogoContext);
  const { mixLayout, toggleSidebar, toggleIcon, layout, layoutURL } = useContext(CustomizerContext);
  const [role, setRole] = useState('');

  const openCloseSidebar = () => {
    toggleSidebar(!toggleIcon);
  };

  const layout1 = localStorage.getItem("sidebar_layout") || layout;

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
    <div className='logo-wrapper responsive-logo-wrapper '>
      {layout1 !== 'compact-wrapper dark-sidebar' && layout1 !== 'compact-wrapper color-sidebar' && mixLayout ? (
        <Link to={getDashboardURL()}>
          <Image attrImage={{ className: 'imgs-fluid custom-logo-style img-fluid-responsive d-inline', src: logo || CubaIcon, alt: 'Company Logo' }} />
        </Link>
      ) : (
        <Link to={getDashboardURL()}>
          <Image attrImage={{ className: 'imgs-fluid custom-logo-style img-fluid-responsive d-inline', src: logo || CubaIcon, alt: 'Company Logo' }} />
        </Link>
      )}
      <div className='back-btn' onClick={() => openCloseSidebar()}>
        <i className='fa fa-angle-left'></i>
      </div>
      <div className='toggle-sidebar' onClick={openCloseSidebar}>
        <Grid className='status_toggle middle sidebar-toggle' />
      </div>
    </div>
  );
};

export default SidebarLogo;
