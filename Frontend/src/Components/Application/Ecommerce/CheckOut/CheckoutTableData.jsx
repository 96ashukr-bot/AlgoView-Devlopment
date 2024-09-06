import React, { Fragment, useContext } from 'react';
import { FirstName, LastName, Phone, EmailAddress, Country, CountryMenu, Address, TownCity, StateCountry, PostalCode, CheckMeOut, PlaceOrder, } from '../../../../Constant';
import { Btn } from '../../../../AbstractElements';
import { Col, Form, FormGroup, Input, Label, Row } from 'reactstrap';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import CustomizerContext from '../../../../_helper/Customizer';

const CheckoutTableData = () => {
    const { layoutURL } = useContext(CustomizerContext);
    const history = useNavigate();
    const onSubmit = (data) => {
        if (data !== '') {
            alert('You submitted the form and stuff!');
            history(`/app/ecommerce/invoice/${layoutURL}`);
        } else {
            errors.alert('add data');
        }
    };
    const { register, formState: { errors }, handleSubmit } = useForm();
    return (
        <Fragment>
            <Col xl="6" sm="12">
                <Form onSubmit={handleSubmit(onSubmit)} className="needs-validation" >
                    <Row>
                        <FormGroup className="mb-3 col-sm-6">
                            <Label>{FirstName}</Label>
                            <input className="form-control" type="text" name="firstName" {...register('firstName', { required: true })} />
                            <span style={{ color: '#ff5370' }}>{errors.firstName && 'First name is required'}</span>
                        </FormGroup>
                        <FormGroup className="mb-3 col-sm-6">
                            <Label>{LastName}</Label>
                            <input className="form-control" type="text" name="lastName" {...register('lastName', { required: true })} />
                            <span style={{ color: '#ff5370' }}>{errors.lastName && 'Last name is required'}</span>
                        </FormGroup>
                    </Row>
                    <Row>
                        <FormGroup className="mb-3 col-sm-6">
                            <Label>{Phone}</Label>
                            <input className="form-control" type="number" name="phone" {...register('phone', { required: true })} />
                            <span style={{ color: '#ff5370' }}>{errors.phone && 'Please enter number for phone.'}</span>
                        </FormGroup>
                        <FormGroup className="mb-3 col-sm-6">
                            <Label>{EmailAddress}</Label>
                            <input className="form-control" type="text" name="email" {...register('email', { required: true, pattern: /^\S+@\S+$/i })} />
                            <span style={{ color: '#ff5370' }}>{errors.email && 'Please enter proper email address .'}</span>
                        </FormGroup>
                    </Row>
                    <FormGroup className="mb-3">
                        <Label>{Country}</Label>
                        <Input className="form-control" type="select" name="selectMulti">
                            {CountryMenu.map((items, i) =>
                                <option key={i}>{items}</option>
                            )}
                        </Input>
                    </FormGroup>
                    <FormGroup className="mb-3">
                        <Label for="inputAddress5">{Address}</Label>
                        <input className="form-control" type="text" name="address" {...register('address', { required: true, min: 20, max: 120 })} />
                        <span style={{ color: '#ff5370' }}>{errors.address && 'Please right your address .'}</span>
                    </FormGroup>
                    <FormGroup className="mb-3">
                        <Label for="inputCity">{TownCity}</Label>
                        <input className="form-control" type="text" name="city" {...register('city', { required: true })} />
                        <span style={{ color: '#ff5370' }}>{errors.city && 'select one city'}</span>
                    </FormGroup>
                    <FormGroup className="mb-3">
                        <Label for="inputAddress2">{StateCountry}</Label>
                        <input className="form-control" type="text" name="state" {...register('state', { required: true })} />
                        <span style={{ color: '#ff5370' }}>{errors.state && 'select one state'}</span>
                    </FormGroup>
                    <FormGroup className="mb-3">
                        <Label for="inputAddress6">{PostalCode}</Label>
                        <input className="form-control" type="text" name="pincode" {...register('pincode', { pattern: /\d+/ })} />
                        <span style={{ color: '#ff5370' }}>{errors.pincode && 'Required integer'}</span>
                    </FormGroup>
                    <FormGroup className="mb-3">
                        <div className="form-check">
                            <Input type="checkbox" className="form-check-input checkbox_animated" />
                            <Label>{CheckMeOut}</Label>
                        </div>
                    </FormGroup>
                    <div>
                        <div className="text-end"><Btn attrBtn={{ type: 'submit', color: 'primary' }}>{PlaceOrder}</Btn> </div>
                    </div>
                </Form>
            </Col>
        </Fragment>
    );
};
export default CheckoutTableData;