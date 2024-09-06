import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { VaryingModalContent } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import ModalButton from './common/ModalButton';

const VaryingContent = () => {

  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={VaryingModalContent} />
        <CardBody>
          <div className="btn-showcase">
            <ModalButton btnText='Open modal for @mdo' defaultVal='@fat' />
            <ModalButton btnText='Open modal for @fat' defaultVal='@Mat' />
            <ModalButton btnText='Open modal for @getbootstrap' defaultVal='@getbootstrap' />
          </div>
        </CardBody>
      </Card>
    </Col>

  );
};

export default VaryingContent;