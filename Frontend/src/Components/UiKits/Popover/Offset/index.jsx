import React, { useState } from 'react';
import { Card, CardBody, CardHeader, Col, Popover, PopoverBody, PopoverHeader } from 'reactstrap';
import { Btn } from '../../../../AbstractElements';
import { OffsetToTooltip } from '../../../../Constant';
import { OffsetPopoverData } from '../../../Common/Data/Ui-kits';
import CommonPopover from '../common/CommonPopover';

const Offset = () => {
  const [popover, setPopover] = useState(false);
  const Toggle = () => setPopover(!popover);

  return (
    <Col sm="12">
      <Card>
        <CardHeader>
          <h5>{OffsetToTooltip}</h5><span>{'lorem ipsum dolor sit amet, consectetur adipisicing elit'}</span>
        </CardHeader>
        <CardBody>
          <div className="btn-showcase">
            <Btn attrBtn={{ color: 'primary', className: 'example-popover', id: 'Popover-12' }}>20px 20px</Btn>
            <Popover
              placement='top'
              isOpen={popover}
              target='Popover-12'
              offset={[20,20]}
              toggle={Toggle}
            >
              <PopoverHeader>Popover title</PopoverHeader>
              <PopoverBody>
                Vivamus sagittis lacus vel augue laoreet rutrum faucibus.
              </PopoverBody>
            </Popover>
            {OffsetPopoverData.map((popover) => {
              return <CommonPopover key={popover.id} item={popover} />;
            })}
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default Offset;