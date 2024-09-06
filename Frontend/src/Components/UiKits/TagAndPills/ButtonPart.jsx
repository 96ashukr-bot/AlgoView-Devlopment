import React from 'react';
import { CardBody, CardHeader, Col } from 'reactstrap';
import { Mail, Bell, Settings, Music, AlertTriangle, AlertCircle } from 'react-feather';
import { Badges, Btn, H5 } from '../../../AbstractElements';
import { Messages, Notification } from '../../../Constant';

const ButtonPart = () => {
  return (
    <Col sm="12" xl="6">
      <div className="card height-equal">
        <CardHeader>
          <H5>{'Badges as part buttons'}</H5>
        </CardHeader>
        <CardBody>
          <div className="mb-3">
            <Btn attrBtn={{ color: 'primary' }} >
              {Messages} <Badges attrBadge={{ className: 'badge rounded-pill badge-light text-dark', color: 'light', pill: true }} ><Mail /></Badges>
            </Btn>
          </div>
          <div className="mb-3">
            <Btn attrBtn={{ color: 'secondary', type: 'button' }} >
              {Notification} <Badges attrBadge={{ className: 'badge rounded-pill badge-light text-dark', color: 'light', pill: true }} ><Bell /></Badges></Btn>
          </div>
          <div className="mb-3">
            <Btn attrBtn={{ color: 'success' }} >{'Update available'} <Badges attrBadge={{ className: 'badge rounded-pill badge-light text-dark', color: 'light', pill: true }} ><Settings /></Badges></Btn>
          </div>
          <div className="mb-3">
            <Btn attrBtn={{ color: 'info' }} >{'Playing Now'} <Badges attrBadge={{ className: 'badge rounded-pill badge-light text-dark', color: 'light', pill: true }} ><Music /></Badges></Btn>
          </div>
          <div className="mb-3">
            <Btn attrBtn={{ color: 'warning' }} >{'1.2 GB Used'} <Badges attrBadge={{ className: 'badge rounded-pill badge-light text-dark', color: 'light', pill: true }} ><AlertTriangle /></Badges></Btn>
          </div>
          <div>
            <Btn attrBtn={{ color: 'danger' }} >{'Alert'} <Badges attrBadge={{ className: 'badge rounded-pill badge-light text-dark', color: 'light', pill: true }} ><AlertCircle /></Badges></Btn>
          </div>
        </CardBody>
      </div>
    </Col>
  );
};

export default ButtonPart;