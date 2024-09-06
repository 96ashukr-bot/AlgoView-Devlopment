import React, { useState } from 'react';
import { Card, CardBody, Col, Popover, PopoverBody, PopoverHeader } from 'reactstrap';
import { Btn } from '../../../../AbstractElements';
import { Direction } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import { DirectionData } from '../../../Common/Data/Ui-kits';
import CommonPopover from '../common/CommonPopover';

const Directions = () => {
  const [popover, setPopover] = useState(false);
  const Toggle = () => setPopover(!popover);

  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={Direction} span1="lorem ipsum dolor sit amet, consectetur adipisicing elit" />
        <CardBody>
          <div className="btn-showcase">
            <Btn attrBtn={{ color: 'primary', className: 'example-popover', id: 'Popover-4' }}>Popover on top</Btn>
            <Popover
              placement='top'
              isOpen={popover}
              target='Popover-4'
              toggle={Toggle}
            >
              <PopoverHeader>Popover title</PopoverHeader>
              <PopoverBody>
                Vivamus sagittis lacus vel augue laoreet rutrum faucibus.
              </PopoverBody>
            </Popover>
            {DirectionData.map((popover) => {
              return <CommonPopover key={popover.id} item={popover} />;
            })}
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default Directions;