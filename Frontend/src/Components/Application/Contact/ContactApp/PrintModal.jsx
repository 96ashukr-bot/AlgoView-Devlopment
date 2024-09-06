import React, { Fragment, useRef } from 'react';
import { Button, Modal, ModalBody, ModalHeader } from 'reactstrap';
import { Cancel, PrintViews, Print } from '../../../../Constant';
import PrintPreview from '../PrintPreview';
import ReactToPrint from 'react-to-print';
import { Btn } from '../../../../AbstractElements';

const PrintModal = ({ printmodal, selectedUser, toggleCallback }) => {
    const printModalToggle = () => {
        toggleCallback(false);
    };

    const componentRef = useRef();
    return (
        <Fragment>
            <Modal isOpen={printmodal} toggle={printModalToggle} >
                <ModalHeader toggle={printModalToggle}>{PrintViews}</ModalHeader>
                <ModalBody className="list-persons">
                    <PrintPreview selectedUser={selectedUser} ref={componentRef} />
                    <ReactToPrint
                        trigger={() => (
                            <Button color="secondary" className="me-1">
                                {Print}
                            </Button>
                        )}
                        content={() => componentRef.current}
                    />
                    <Btn attrBtn={{ color: 'primary', onClick: printModalToggle }} >{Cancel}</Btn>
                </ModalBody>
            </Modal>
        </Fragment>
    );
};

export default PrintModal;