import React, { useState } from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Btn, H5, ToolTip } from '../../../../AbstractElements';
import { Direction } from '../../../../Constant';
import CommonTooltip from './CommonTooltip';

const Directions = () => {
  const [tooltip, setTooltip] = useState(false);
  const toggle = () => setTooltip(!tooltip);

  const Data = [
    {
      id: 2,
      placement: 'right',
      tooltip: 'Tooltip on right'
    },
    {
      id: 3,
      placement: 'bottom',
      tooltip: 'Tooltip on bottom'
    },
    {
      id: 4,
      placement: 'left',
      tooltip: 'Tooltip on left'
    }
  ];
  return (
    <Col sm="12">
      <Card>
        <CardHeader>
          <H5>{Direction}</H5>
        </CardHeader>
        <CardBody>
          <div className="btn-showcase">
            <Btn attrBtn={{ color: 'primary', id: 'Tooltip-1' }}>Tooltip on top</Btn>
            <ToolTip
              attrToolTip={{
                placement: 'top',
                isOpen: tooltip,
                target: 'Tooltip-1',
                toggle: toggle
              }} >
              Tooltip on top
            </ToolTip>
            {Data.map((item) =>
              <CommonTooltip key={item.id} item={item} />
            )}
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default Directions;