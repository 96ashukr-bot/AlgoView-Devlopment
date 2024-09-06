import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, P } from '../../../../AbstractElements';
import { TextColor } from '../../../../Constant';

const TextColorCard = () => {
  return (
    <Col sm="12" xl="6">
      <Card>
        <CardHeader>
          <H5>{TextColor}</H5><span>{'You can Give text color by using txt-* className'}</span>
        </CardHeader>
        <CardBody>
          <P attrPara={{ className: 'txt-primary' }}>{'This is Primary text You can archive this adding'} <code>{'.txt-primary'}</code>{' class'}</P>
          <P attrPara={{ className: 'txt-secondary' }}>{'This is Secondary text You can archive this adding'} <code>{'.txt-secondary'}</code>{' class'}</P>
          <P attrPara={{ className: 'txt-success' }}>{'This is Success text You can archive this adding'} <code>{'.txt-success'}</code>{' class'}</P>
          <P attrPara={{ className: 'txt-info' }}>{'This is Info text You can archive this adding'} <code>{'.txt-info'}</code>{' class'}</P>
          <P attrPara={{ className: 'txt-warning' }}>{'This is Warning text You can archive this adding'} <code>{'.txt-warning'}</code>{' class'}</P>
          <P attrPara={{ className: 'txt-danger' }}>{'This is Danger text You can archive this adding'} <code>{'.txt-danger'}</code>{' class'}</P>
          <P attrPara={{ className: 'txt-dark' }}>{'This is Dark text You can archive this adding'} <code>{'.txt-dark'}</code>{' class'}</P>
          <P attrPara={{ className: 'txt-primary' }}>{'This is Primary text You can archive this adding'} <code>{'.txt-primary'}</code>{' class'}</P>
        </CardBody>
      </Card>
    </Col>
  );
};

export default TextColorCard;