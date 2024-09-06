import React, { useState } from "react";
import { Card, CardBody, CardHeader, Col } from "reactstrap";
import { Alerts, Btn, H5, P } from "../../../AbstractElements";
import { TextAsAction } from "../../../Constant";
import { TextAsActionsData } from "../../Common/Data/Ui-kits";
import CommonAlert from "./Common/CommonAlert";

const TextAsActions = () => {
  const [Open, setOpen] = useState(true);
  const Toggle = () => setOpen(!Open);

  return (
    <Col sm="12" xl="6">
      <Card className="height-equal" style={{ minHeight: "708px" }}>
        <CardHeader>
          <H5>{TextAsAction}</H5>
          <span>
            {"Use the"} <code>{".alert-link"}</code> {"utility class to quickly provide matching colored links within any alert"}
          </span>
        </CardHeader>
        <CardBody className="dismiss-text">
          <Alerts attrAlert={{ color: "primary inverse alert-dismissible ", isOpen: Open, target: "Alert-1" }}>
            <i className="icon-timer"></i>
            <P>
              {"Your time Over after"} <b>{"5"}</b> {"miniute"}
              <Btn attrBtn={{ className: "btn-close", color: "transperant", id: "Alert-1", onClick: Toggle }}>
                <span className="bg-primary">{"dismiss"}</span>
              </Btn>
            </P>
          </Alerts>
          {TextAsActionsData.map((data) => (
            <CommonAlert key={data.id} item={data} btnText={true} />
          ))}
        </CardBody>
      </Card>
    </Col>
  );
};

export default TextAsActions;
