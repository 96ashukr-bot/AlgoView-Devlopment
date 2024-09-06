import React, { useState } from 'react';
import { Clock } from 'react-feather';
import { Card, CardBody, Col } from 'reactstrap';
import { Alerts, P } from '../../../AbstractElements';
import { AlertWithIcon } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';
import { IconsWithOutlineData } from '../../Common/Data/Ui-kits';
import CommonAlert from './Common/CommonAlert';

const IconsWithOutline = () => {
  const [Open, setOpen] = useState(true);
  const Toggle = () => setOpen(!Open);

  return (
    <Col sm="12" xl="6">
      <Card className="height-equal" style={{ minHeight: '708px' }}>
        <HeaderCard title={AlertWithIcon} span1={'Just add Any icon before text'} />
        <CardBody>
          <Alerts attrAlert={{
            className: 'alert-dismissible', color: 'primary outline',
            isOpen: Open,
            target: 'Alert-1',
          }}
            closeBtn={true}
            attrBtn={{ className: 'btn-close', color: 'default', id: 'Alert-1', onClick: Toggle }}>
            <Clock />
            <P>You can check in on some of those fields below.</P>
          </Alerts>
          {IconsWithOutlineData.map((data) =>
            <CommonAlert key={data.id} item={data} />
          )}
        </CardBody>
      </Card>
    </Col>
  );
};

export default IconsWithOutline;