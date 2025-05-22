import React, { Fragment, useState, useLayoutEffect, useContext } from "react";
import { Col } from "reactstrap";
import { AlignCenter } from "react-feather";
import { Link } from "react-router-dom";
import { Image } from "../../../AbstractElements";
import CustomizerContext from "../../../_helper/Customizer";
// import NotificationSlider from "./NotificationSlider";

const Leftbar = () => {
  const { layoutURL, setToggleIcon, toggleSidebar } = useContext(CustomizerContext);
  const [sidebartoggle, setSidebartoggle] = useState(true);
  const [width, setWidth] = useState(window.innerWidth);

  useLayoutEffect(() => {
    const updateSize = () => {
      setWidth(window.innerWidth);
      setToggleIcon(window.innerWidth <= 991);
    };

    window.addEventListener("resize", updateSize);
    updateSize();

    return () => window.removeEventListener("resize", updateSize);
  }, [setToggleIcon]);

  const responsive_openCloseSidebar = (toggle) => {
    const sidebarWrapper = document.querySelector(".sidebar-wrapper");
    const overlay = document.querySelector(".bg-overlay1");

    if (width <= 991) {
      if (toggle) {
        sidebarWrapper?.classList.add("close_icon");
        overlay?.classList.remove("active");
      } else {
        sidebarWrapper?.classList.remove("close_icon");
        overlay?.classList.add("active");
      }

      toggleSidebar(!toggle);
      setSidebartoggle(!toggle);
    } else {
      if (toggle) {
        sidebarWrapper?.classList.add("close_icon");
      } else {
        sidebarWrapper?.classList.remove("close_icon");
      }

      toggleSidebar(!toggle);
      setSidebartoggle(!toggle);
    }
  };

  return (
    <Fragment>
      <Col className="header-logo-wrapper col-auto p-0" id="out_side_click">
        <div className="logo-wrapper">
          <Link to={`/dashboard/algoviewtech/admin`}>
            <Image
              attrImage={{
                className: "img-fluid for-light",
                src: `${require("../../../assets/images/logo/logo.png")}`,
                alt: "",
              }}
            />
            <Image
              attrImage={{
                className: "img-fluid for-dark",
                src: `${require("../../../assets/images/logo/logo_dark.png")}`,
                alt: "",
              }}
            />
          </Link>
        </div>
        <div className="toggle-sidebar" onClick={() => responsive_openCloseSidebar(sidebartoggle)}
          style={{ display: width > 0 && width <= 991 ? "block" : "none" }}
        >
          <AlignCenter className="status_toggle middle sidebar-toggle" id="sidebar-toggle" />
        </div>
      </Col>
      <Col xxl="5" xl="6" lg="5" md="4" sm="3" className="left-header p-0">
        {/* <NotificationSlider /> */}
      </Col>
    </Fragment>
  );
};

export default Leftbar;
