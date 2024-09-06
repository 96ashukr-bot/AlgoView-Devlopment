import React, { Fragment, useState } from "react";
import { Card, CardBody, CardHeader, Col } from "reactstrap";
import { H5 } from "../../../../AbstractElements";
import Commen from "./Commen";

const Postfix = () => {
    const [val, setVal] = useState(30)
    const post = "%"
    return (
        <Fragment>
            <Col sm="12" md="6">
                <Card>
                    <CardHeader>
                        <H5 attrH5={{ className: "card-title" }}>Touchspin with Postfix</H5><span>Add <code>.data-bts-postfix="POSTFIX_VALUE"</code> attribute to input to add postfix to touchspin input
                            group.</span>
                    </CardHeader>
                    <CardBody>
                        <Commen val={val} setVal={setVal} post={post} />
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}
export default Postfix