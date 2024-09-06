import React, { Fragment, useState } from 'react';
import { Btn, P } from '../../../../../AbstractElements';
import { ModalTitle, VerticallyCentered } from '../../../../../Constant';
import CommonModal from '../../common/modal';

const VerticalBtn = () => {
  const [modal, setModal] = useState(false);
  const toggle = () => setModal(!modal);
  return (
    <Fragment>
      <Btn attrBtn={{ color: 'primary', onClick: toggle }} >{VerticallyCentered}</Btn>
      <CommonModal isOpen={modal} title={ModalTitle} toggler={toggle} >
        <P>{'Cras mattis consectetur purus sit amet fermentum. Cras justo odio, dapibus ac facilisis in, egestas eget quam. Morbi leo risus, porta ac consectetur ac, vestibulum at eros.'}</P>
      </CommonModal>
    </Fragment>
  );
};

export default VerticalBtn;