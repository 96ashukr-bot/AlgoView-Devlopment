import React, { useState } from 'react';
import { Clock } from 'react-feather';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Alerts, H5, P } from '../../../AbstractElements';
import { AlertWithIcon } from '../../../Constant';
import { dataWithIcon } from '../../Common/Data/Ui-kits';
import CommonAlert from './Common/CommonAlert';

const AlertWithIcons = () => {
  const [Open, setOpen] = useState(true);
  const Toggle = () => setOpen(!Open);

  return (
    <Col sm="12" xl="6">
      <Card className="height-equal" style={{ minHeight: '708px' }}>
        <CardHeader>
          <H5>{AlertWithIcon}</H5><span>{'Just add Any icon before text'}</span>
        </CardHeader>
        <CardBody>
          <Alerts attrAlert={{
            className: 'alert-dismissible', color: 'primary dark',
            isOpen: Open,
            target: 'Alert-1',
          }}
            closeBtn={true}
            attrBtn={{ className: 'btn-close', color: 'default', id: 'Alert-1', onClick: Toggle }}>
            <Clock />
            <P>You can check in on some of those fields below.</P>
          </Alerts>
          {dataWithIcon.map((data) =>
            <CommonAlert key={data.id} item={data} />
          )}
        </CardBody>
      </Card>
    </Col>
  );
};

export default AlertWithIcons;