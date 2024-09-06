import React, { useState } from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Btn, H5, ToolTip } from '../../../../AbstractElements';
import { HTMLElements } from '../../../../Constant';
import HtmlContentTooltip from './HtmlContentTooltip';

const HtmlElement = () => {
  const [tooltip, setTooltip] = useState(false);
  const toggle = () => setTooltip(!tooltip);
  const tooltips = <>{'Tooltip'} <b>with</b> <code>HTML</code></>;
  const Data = [
    {
      id: 6,
      placement: 'right',
      btntext: 'Click me',
      tooltip: tooltips
    },
    {
      id: 7,
      placement: 'bottom',
      btntext: 'Click me',
      tooltip: tooltips
    },
    {
      id: 8,
      placement: 'left',
      btntext: 'Click me',
      tooltip: tooltips
    }
  ];
  return (
    <Col sm="12">
      <Card>
        <CardHeader>
          <H5>{HTMLElements}</H5>
        </CardHeader>
        <CardBody>
          <div className="btn-showcase">
            <Btn attrBtn={{ color: 'primary', id: 'Tooltip-5', onClick: toggle }}>Click me</Btn>
            <ToolTip
              attrToolTip={{
                placement: 'top',
                isOpen: tooltip,
                target: 'Tooltip-5',
              }} >
              {tooltips}
            </ToolTip>
            {Data.map((item) =>
              <HtmlContentTooltip key={item.id} item={item} />
            )}
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default HtmlElement;