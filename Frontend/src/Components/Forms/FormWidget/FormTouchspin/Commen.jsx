import React, { Fragment } from 'react';
import { Input, InputGroupText } from 'reactstrap';
import { Btn } from '../../../../AbstractElements';

const Commen = (props) => {
  const Minus = () => {
    if (props.decimal) {
      props.setVal(props.val - 0.25);
    } else if (props.step) {
      props.setVal(props.val - 10);
    } else {
      props.setVal(props.val - 1);
    }
  };
  const Addition = () => {
    if (props.decimal) {
      props.setVal(props.val + 0.25);
    } else if (props.step) {
      props.setVal(props.val + 10);
    } else {
      props.setVal(props.val + 1);
    }
  };
  return (
    <Fragment>
      {props.vertical ? (
        <div className='touchspin-vertical-tab'>
          <div className='input-group bootstrap-touchspin'>
            <span className='input-group-text bootstrap-touchspin-prefix' style={{ display: 'none' }} />
            <Input className='touchspin touchspin-vertical text-start' readOnly value={props.val} type='number' name='quantity' placeholder='80' style={{ display: 'block' }} />
            <span className='input-group-text bootstrap-touchspin-postfix' style={{ display: 'none' }} />
            <span className='input-group-btn-vertical'>
              <Btn attrBtn={{ color: 'primary', onClick: Minus, className: 'btn-square bootstrap-touchspin-up' }}>
                <i className='fa fa-angle-up' />
              </Btn>
              <Btn attrBtn={{ color: 'primary', onClick: Addition, className: 'btn-square bootstrap-touchspin-up' }}>
                <i className='fa fa-angle-down' />
              </Btn>
            </span>
          </div>
        </div>
      ) : (
        <div className={`input-group bootstrap-touchspin ${props.groupText ? 'input-group-text-none' : ''}`}>
          <Btn attrBtn={{ color: 'primary', className: 'bootstrap-touchspin-down', onClick: Minus }}>
            <i className='fa fa-minus'></i>
          </Btn>
          {props.pre && <InputGroupText>{props.pre}</InputGroupText>}
          <Input className='touchspin text-start' type='text' name='quantity' style={{ display: 'block' }} value={props.val} readOnly />
          {props.post && <InputGroupText>{props.post}</InputGroupText>}
          <Btn attrBtn={{ color: 'primary btn-square', className: 'bootstrap-touchspin-up', onClick: Addition }}>
            <i className='fa fa-plus'></i>
          </Btn>
        </div>
      )}
    </Fragment>
  );
};
export default Commen;
