import React, { Fragment, useState } from 'react';
import { Row, Col, Card, CardBody, Label, Form } from 'reactstrap';
import { Default, Disabled } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';
import { Range, getTrackBackground } from "react-range";

const DisabledClass = () => {
    const [values3, setValues3] = useState([10]);
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <HeaderCard title={Disabled} />
                    <CardBody>
                        <Form className="theme-form form-label-align-right range-slider">
                            <Row className="mb-0">
                                <Col md="2">
                                    <Label>{Default}</Label>
                                </Col>
                                <Col md="10">
                                    <div
                                        style={{
                                            display: "flex",
                                            justifyContent: "center",
                                            flexWrap: "wrap",
                                            margin: "1em"
                                        }}
                                    >
                                        <Range
                                            values={values3}
                                            step={1}
                                            min={0}
                                            max={20}
                                            onChange={(values3) => setValues3(values3)}
                                            disabled={true}
                                            renderTrack={({ props, children }) => (
                                                <div
                                                    onMouseDown={props.onMouseDown}
                                                    onTouchStart={props.onTouchStart}
                                                    style={{
                                                        ...props.style,
                                                        height: "36px",
                                                        display: "flex",
                                                        width: "100%"
                                                    }}
                                                >
                                                    <output style={{ marginTop: "12px" }}>
                                                        0
                                                    </output>
                                                    <div
                                                        ref={props.ref}
                                                        style={{
                                                            height: "5px",
                                                            width: "100%",
                                                            borderRadius: "4px",
                                                            background: getTrackBackground({
                                                                values: values3,
                                                                colors: ["#ccc", "#ccc"],
                                                                min: 0,
                                                                max: 20
                                                            }),
                                                            alignSelf: "center"
                                                        }}
                                                    >

                                                        {children}
                                                    </div>
                                                    <output style={{ marginTop: "12px" }}>
                                                        20
                                                    </output>
                                                </div>
                                            )}
                                            renderThumb={({ props, isDragged }) => (
                                                <div
                                                    {...props}
                                                    style={{
                                                        ...props.style,
                                                        height: "35px",
                                                        width: "35px",
                                                        borderRadius: "30px",
                                                        backgroundColor: "#FFF",
                                                        display: "flex",
                                                        justifyContent: "center",
                                                        alignItems: "center",
                                                        boxShadow: "0px 2px 6px #AAA"
                                                    }}
                                                >
                                                    <div
                                                        style={{
                                                            height: "16px",
                                                            width: "5px",
                                                            backgroundColor: isDragged ? "#ccc" : "#CCC"
                                                        }}
                                                    />
                                                </div>
                                            )}
                                        />
                                        <output style={{ marginTop: "12px" }} id="output">
                                            {values3[0]}
                                        </output>
                                    </div>
                                </Col>
                            </Row>
                        </Form>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default DisabledClass;