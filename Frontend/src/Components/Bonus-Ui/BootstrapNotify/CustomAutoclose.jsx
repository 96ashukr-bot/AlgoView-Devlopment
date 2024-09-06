import React, { Fragment } from "react";
import { Col, Card, CardBody, CardHeader } from "reactstrap";
import { toast } from "react-toastify";
import { CustomAutoclose, AutoCloseIn1000Sec, AutoCloseIn15000Sec, AutoCloseIn500Sec, AutoCloseIn5000Sec } from "../../../Constant";
import { Btn, H5 } from "../../../AbstractElements";

// toast.configure();

const CustomAutocloseClass = () => {
  const autoclosetoaster = (toastname) => {
    switch (toastname) {
      case "autoclose1Toast":
        toast.success("Success Notification !", {
          position: toast.POSITION.TOP_RIGHT,
          autoClose: 15000,
        });
        break;
      case "autoclose2Toast":
        toast.info("Info Notification !", {
          position: toast.POSITION.TOP_RIGHT,
          autoClose: 5000,
        });
        break;
      case "autoclose3Toast":
        toast.warn("Warning Notification !", {
          position: toast.POSITION.TOP_RIGHT,
          autoClose: 1000,
        });
        break;
      case "autoclose4Toast":
        toast.error("Danger Notification !", {
          position: toast.POSITION.TOP_RIGHT,
          autoClose: 500,
        });
        break;
      default:
        break;
    }
  };
  return (
    <Fragment>
      <Col sm="12">
        <Card>
          <CardHeader>
            <H5>{CustomAutoclose}</H5>
          </CardHeader>
          <CardBody>
            <div className="btn-showcase">
              <Btn attrBtn={{ name: "autoclose1Toast", color: "success", onClick: (e) => autoclosetoaster(e.target.name) }}>{AutoCloseIn15000Sec}</Btn>
              <Btn attrBtn={{ name: "autoclose2Toast", color: "info", onClick: (e) => autoclosetoaster(e.target.name) }}>{AutoCloseIn5000Sec}</Btn>
              <Btn attrBtn={{ name: "autoclose3Toast", color: "warning", onClick: (e) => autoclosetoaster(e.target.name) }}>{AutoCloseIn1000Sec}</Btn>
              <Btn attrBtn={{ name: "autoclose4Toast", color: "danger", onClick: (e) => autoclosetoaster(e.target.name) }}>{AutoCloseIn500Sec}</Btn>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};

export default CustomAutocloseClass;
