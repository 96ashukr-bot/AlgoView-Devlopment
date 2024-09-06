import React, { Fragment } from 'react';
import { Form, FormGroup, Input, Label, Modal, ModalBody, Button } from 'reactstrap';
import { Btn, H5 } from '../../../AbstractElements';
import { Cancel, Save } from '../../../Constant';

const ModalTag = (props) => {
  return (
    <Fragment>
      <Modal className='fade show modal-bookmark' size='lg' isOpen={props.value} toggle={props.tagToggle}>
        <div className='modal-header'>
          <H5 attrH5={{ className: 'modal-title' }}>{'Create Tag'}</H5>
          <Button color='transparent' className='btn-close float-end' onClick={props.tagToggle} type='button' data-bs-dismiss='modal' aria-label='Close'></Button>
        </div>
        <ModalBody>
          <Form className='form-bookmark needs-validation'>
            <div className='form-row'>
              <FormGroup className='col-md-12'>
                <Label>{'Tag Name'}</Label>
                <Input type='text' />
              </FormGroup>
              <FormGroup className='col-md-12 mb-0'>
                <Label>{'Tag color'}</Label>
                <Input type='color' className='fill-color' defaultValue='#563d7c' />
              </FormGroup>
            </div>
            <Btn
              attrBtn={{
                color: 'secondary',
                onClick: props.tagToggle,
              }}>
              {Save}
            </Btn>
            <Btn
              attrBtn={{
                color: 'primary m-l-5',
                onClick: props.tagToggle,
              }}>
              {Cancel}
            </Btn>
          </Form>
        </ModalBody>
      </Modal>
    </Fragment>
  );
};
export default ModalTag;
