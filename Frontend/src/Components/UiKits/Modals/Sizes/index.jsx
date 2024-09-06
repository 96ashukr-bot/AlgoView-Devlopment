import React, { useState } from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { Btn } from '../../../../AbstractElements';
import { LargeModal, SizesModal, SmallModal } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import CommonModal from '../common/modal';

const SizesModals = () => {
  const [Large, setLarge] = useState(false);
  const [Small, setSmall] = useState(false);

  const LargeModaltoggle = () => setLarge(!Large);
  const SmallModaltoggle = () => setSmall(!Small);
  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={SizesModal} />
        <CardBody>
          <div className="btn-showcase">
            <Btn attrBtn={{ color: "primary", onClick: LargeModaltoggle }}>{LargeModal}</Btn>
            <CommonModal isOpen={Large} title={LargeModal} toggler={LargeModaltoggle} size="lg">...</CommonModal>
            <Btn attrBtn={{ color: "primary", onClick: SmallModaltoggle }} >{SizesModal}</Btn>
            <CommonModal isOpen={Small} title={SmallModal} toggler={SmallModaltoggle} size="sm">...</CommonModal>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default SizesModals;