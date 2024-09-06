import React, { Fragment, useContext, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Modal, ModalHeader, ModalBody, Form, FormGroup, Label } from 'reactstrap';
import { AddTask, TaskTitle, Collection, General, Description, Save, Cancel, NewTask } from '../../../Constant';
import { CheckCircle } from 'react-feather';
import { Btn } from '../../../AbstractElements';
import TaskContext from '../../../_helper/Task';

const NewTaskClass = () => {
    const { AddNewTask } = useContext(TaskContext);
    const { register, handleSubmit, formState: { errors } } = useForm();
    const [addModal, setaddModal] = useState(false);
    const addToggle = () => {
        setaddModal(!addModal);
    };

    const Addtask = data => {
        if (data !== '') {
            AddNewTask(data);
            setaddModal(false);
        } else {
            errors.showMessages();
        }
    };

    return (
        <Fragment>
            <button className="badge-light-primary d-block w-100 btn-mail" onClick={addToggle}><CheckCircle className="me-2" />{NewTask}</button>
            <Modal className="modal-bookmark" isOpen={addModal} toggle={addToggle} size="lg">
                <ModalHeader toggle={addToggle}>{AddTask}</ModalHeader>
                <ModalBody>
                    <Form className="form-bookmark needs-validation" onSubmit={handleSubmit(Addtask)}>
                        <div className="form-row">
                            <FormGroup className="col-md-12">
                                <Label>{TaskTitle}</Label>
                                <input className="form-control" name="title" type="text" {...register('title', { required: true })} />
                                <span style={{ color: 'red' }}>{errors.title && 'Title is required'}</span>
                            </FormGroup>
                            <FormGroup className="col-md-12">
                                <Label>{Collection}</Label>
                                <select className="js-example-basic-single form-control" name="collection" type="select" {...register('collection', { required: true })}>
                                    <option value="general">{General}</option>
                                    <option value="fs">{'Fs'}</option>
                                </select>
                            </FormGroup>
                            <FormGroup className="col-md-12">
                                <Label>{Description}</Label>
                                <input className="form-control" name="desc" type="textarea" {...register('desc', { required: true })}></input>
                                <span style={{ color: 'red' }}>{errors.desc && 'Description is required'}</span>
                            </FormGroup>
                        </div>
                        <Btn attrBtn={{ color: 'secondary', className: 'me-2' }}>{Save}</Btn>
                        <Btn attrBtn={{ color: 'primary', onClick: addToggle }} >{Cancel}</Btn>
                    </Form>
                </ModalBody>
            </Modal>
        </Fragment>
    );
};
export default NewTaskClass;