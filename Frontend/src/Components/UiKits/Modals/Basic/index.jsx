import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { BasicModal } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import BasicBtn from './BasicButton';
import GridModal from './GridButton';
import ScrollBtn from './ScrollButton';
import TooltipModal from './Tooltip&Popover';
import VerticalBtn from './VerticalButton/VerticalBtn';

const BasicModals = () => {
  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={BasicModal} />
        <CardBody>
          <div className="btn-showcase">
            <BasicBtn />
            <ScrollBtn />
            <VerticalBtn />
            <TooltipModal />
            <GridModal />
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default BasicModals;