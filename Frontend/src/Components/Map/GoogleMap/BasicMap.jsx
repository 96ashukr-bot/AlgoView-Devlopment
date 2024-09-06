import React, { Fragment } from "react";
import { Card, Col, CardBody } from "reactstrap";
import { GoogleMap, useJsApiLoader } from "@react-google-maps/api";
import HeaderCard from "../../Common/Component/HeaderCard";
import { BasicDemo } from "../../../Constant";

const containerStyle = {
  height: "500px",
};

const center = {
  lat: -3.745,
  lng: -38.523,
};

const BasicMapComp = () => {
  const { isLoaded } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey: "https://maps.googleapis.com/maps/api/js?key=AIzaSyBkNaAGLEVq0YLQMi-PYEMabFeREadYe1Q&v=3.exp&libraries=geometry,drawing,places",
  });
  return (
    <Fragment>
      <Col xl="6" md="12">
        <Card>
          <HeaderCard title={BasicDemo} />
          <CardBody>
            <div className="map-js-height">
              <div id="gmap-simple" className="map-block">
                {isLoaded ? <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={10}></GoogleMap> : "Loading..."}
              </div>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};

export default React.memo(BasicMapComp);
