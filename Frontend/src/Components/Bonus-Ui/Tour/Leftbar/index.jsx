import React, { Fragment, useEffect } from "react";
import { Row } from "reactstrap";
import Followers from "./Followers";
import AboutMe from "./AboutMe";
import Followings from "./Followings";
import LatestPhotos from "./LatestPhoto";
import Friends from "./Friends";
import { useTour } from "@reactour/tour";

const LeftbarProfile = ({ colClass }) => {
  const { setIsOpen } = useTour();
  useEffect(() => {
    var timer = setTimeout(() => {
      setIsOpen(true);
    }, 1000);
    return () => {
      clearTimeout(timer);
    };
  }, []);
  return (
    <Fragment>
      <div className="default-according style-1 faq-accordion job-accordion">
        <Row>
          <AboutMe colClass="col-xl-12" />
          <Followers colClass={colClass} />
          <Followings colClass={colClass} />
          <LatestPhotos colClass={colClass} />
          <Friends colClass={colClass} />
        </Row>
      </div>
    </Fragment>
  );
};

export default LeftbarProfile;
