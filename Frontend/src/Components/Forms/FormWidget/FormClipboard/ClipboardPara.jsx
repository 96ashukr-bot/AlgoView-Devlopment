import React, { Fragment, useState } from 'react';
import CopyToClipboard from 'react-copy-to-clipboard';
import { Card, CardBody, Col } from 'reactstrap';
import { Btn, H6, P } from '../../../../AbstractElements';
import HeaderCard from '../../../Common/Component/HeaderCard';

const ClipboardPara = () => {
  const vall = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit,sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.';
  const [state, setState] = useState({
    value: vall,
    copied: false,
  });
  return (
    <Fragment>
      <Col sm='12' md='6'>
        <Card>
          <HeaderCard title={'Clipboard On Paragraph'} />
          <CardBody>
            <div className='clipboaard-container'>
              <P attrPara={{ className: 'card-description' }}>Copy from Paragraph</P>
              <CopyToClipboard text={state.value} onCopy={() => setState({ copied: true })}>
                <H6 attrH6={{ className: 'border rounded f-w-300' }}>{vall}</H6>
              </CopyToClipboard>
              <div className='mt-3 text-end'>
                <CopyToClipboard text={state.value} onCopy={() => setState({ copied: true })}>
                  <Btn attrBtn={{ className: 'btn-clipboard', color: 'primary' }}>
                    <i className='fa fa-copy'></i> Copy
                  </Btn>
                </CopyToClipboard>
              </div>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};
export default ClipboardPara;
