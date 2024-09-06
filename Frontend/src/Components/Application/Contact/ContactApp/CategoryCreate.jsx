import React, { Fragment, useState } from 'react';
import { AddCategory, Cancel, Save } from '../../../../Constant';
import { Form, FormGroup, Input, ModalBody, ModalHeader, Modal } from 'reactstrap';
import { Btn } from '../../../../AbstractElements';

const CategoryCreate = () => {
    const [categoryModal, setCategoryModal] = useState(false);
    const categoryToggle = () => {
        setCategoryModal(!categoryModal);
    };

    return (
        <Fragment>
            <Btn attrBtn={{ color: 'transparent', className: 'btn btn-category', onClick: categoryToggle }} ><span className="title"> + {AddCategory}</span></Btn>
            <Modal isOpen={categoryModal} toggle={categoryToggle}>
                <ModalHeader toggle={categoryToggle}>{AddCategory}</ModalHeader>
                <ModalBody>
                    <Form className="form-bookmark">
                        <div className="form-row">
                            <FormGroup className="mb-3 col-md-12 my-0">
                                <Input className="form-control" type="text" required="" placeholder="Enter category name" autoComplete="off" />
                            </FormGroup>
                        </div>
                        <Btn attrBtn={{ color: 'secondary', onClick: categoryToggle }} >{Save}</Btn>
                        <Btn attrBtn={{ color: 'primary', className: 'ms-1', onClick: categoryToggle }} >{Cancel}</Btn>
                    </Form>
                </ModalBody>
            </Modal>
        </Fragment>
    );
};

export default CategoryCreate;