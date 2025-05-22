import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import cubaimg from "../../assets/images/logo/logo-icon.png"
import CustomizerContext from '../../_helper/Customizer';

const SidebarIcon = () => {
  const { layoutURL } = useContext(CustomizerContext);
  return (
    <div className="logo-icon-wrapper">
      <Link to={`/dashboard/algoviewtech/admin`}>
        <img
          className="img-fluid"
          src={cubaimg}
          alt=""
        />
      </Link>
    </div>
  );
};

export default SidebarIcon;