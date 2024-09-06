import React, { Fragment, useState, useContext } from 'react';
import { Btn, Image } from '../../../../AbstractElements';
import { useForm } from 'react-hook-form';
import ContactAppContext from '../../../../_helper/Contact';
import { Row, Col, Label, Input, FormGroup, Form } from 'reactstrap';
import { Name, Age, Mobile, Save, Cancel } from '../../../../Constant';

const UpdateUser = ({ editdata, userEditCallback, editurl }) => {
    const { editUser } = useContext(ContactAppContext);
    const { register, handleSubmit, formState: { errors } } = useForm(); // initialise the hook
    const [editUrl, setEditurl] = useState(editurl);

    const UpdateContact = data => {
        if (data !== '') {
            editUser(data, editUrl, editdata.id);
            userEditCallback(false, data, editUrl, true);
        } else {
            errors.showMessages();
        }
    };

    const HandleEditUrl = (event) => {
        if (event.target.files.length === 0)
            return;
        //Image upload validation
        var mimeType = event.target.files[0].type;

        if (mimeType.match(/image\/*/) == null) {
            return;
        }
        // Image upload
        var reader = new FileReader();
        reader.readAsDataURL(event.target.files[0]);
        reader.onload = (_event) => {
            setEditurl(reader.result);
        };
    };

    return (
        <Fragment>
            <div className="contact-editform ps-0 m-auto">
                <Form onSubmit={handleSubmit(UpdateContact)}>
                    <div className="form-row">
                        <div className="contact-profile">
                            <Image attrImage={{ className: 'rounded-circle img-100', src: `${editUrl}`, alt: '' }} />
                            <div className="icon-wrapper">
                                <i className="icofont icofont-pencil-alt-5">
                                    <Input className="upload" type="file" onChange={(e) => HandleEditUrl(e)} />
                                </i>
                            </div>
                        </div>
                        <FormGroup className="col-md-12">
                            <Label>{Name}</Label>
                            <Row>
                                <Col sm="6">
                                    <input className="form-control" type="text" name="name" defaultValue={editdata.name} {...register('name', { required: true })} />
                                    <span style={{ color: 'red' }}>{errors.name && 'First name is required'}</span>
                                </Col>
                                <Col sm="6">
                                    <input className="form-control" type="text" name="surname" defaultValue={editdata.surname} {...register('surname', { required: true })} />
                                    <span style={{ color: 'red' }}>{errors.surname && 'Last name is required'}</span>
                                </Col>
                            </Row>
                        </FormGroup>
                        <FormGroup className="col-md-12">
                            <Label>{Age}</Label>
                            <input className="form-control" type="text" name="age" defaultValue={editdata.age} {...register('age', { required: true, pattern: /\d+/, min: 18, max: 70 })} />
                            <span style={{ color: 'red' }}>{errors.age && 'Please enter age between 18 to 70 year.'}</span>
                        </FormGroup>
                        <FormGroup className="col-md-12">
                            <Label>{Mobile}</Label>
                            <input className="form-control" type="text" name="mobile" defaultValue={editdata.mobile} {...register('mobile', { pattern: /\d+/, minlength: 0, maxlength: 9 })} />
                            <span style={{ color: 'red' }}>{errors.mobile && 'Please enter number max 9 digit'}</span>
                        </FormGroup>
                    </div>
                    <Btn attrBtn={{ color: 'secondary', className: 'update-contact me-1' }} >{Save}</Btn>
                    <Btn attrBtn={{ color: 'primary', onClick: () => userEditCallback(false) }} >{Cancel}</Btn>
                </Form>
            </div>
        </Fragment>
    );
};

export default UpdateUser;