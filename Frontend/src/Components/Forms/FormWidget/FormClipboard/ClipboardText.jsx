import React, { Fragment, useState } from 'react';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import { Button, Card, CardBody, CardHeader, Col, Input } from 'reactstrap';
import { H5, P } from '../../../../AbstractElements';

const ClipboardText = () => {
  const [state, setState] = useState({
    value: '',
    copied: false,
  });
  return (
    <Fragment>
      <Col sm='12' md='6'>
        <Card>
          <CardHeader>
            <H5>Clipboard On Text Input</H5>
          </CardHeader>
          <CardBody>
            <div className='clipboaard-container'>
              <P attrPara={{ className: 'card-description' }}>Cut/copy from text input</P>
              <Input className='form-control' id='clipboardExample1' type='text' placeholder='type some text to copy / cut' value={state.value} onChange={({ target: { value } }) => setState({ value, copied: false })} />
              <div className='mt-3 text-end'>
                <CopyToClipboard text={state.value} onCopy={() => setState({ copied: true })}>
                  <Button className='btn-clipboard me-2' color='primary'>
                    <i className='fa fa-copy'></i> Copy
                  </Button>
                </CopyToClipboard>

                <CopyToClipboard text={state.value} onCopy={() => setState({ copied: true, value: '' })}>
                  <Button className='btn-clipboard-cut' color='secondary'>
                    <i className='fa fa-cut'></i> Cut
                  </Button>
                </CopyToClipboard>
              </div>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};
export default ClipboardText;
