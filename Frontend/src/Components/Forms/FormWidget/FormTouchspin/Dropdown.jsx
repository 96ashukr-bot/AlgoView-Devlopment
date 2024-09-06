import React, { Fragment, useState } from "react";
import { Card, CardBody, CardHeader, Col } from "reactstrap";
import { H5 } from "../../../../AbstractElements";
import Commen from "./Commen";

const DropdownTouchspin = () => {
    const [val, setVal] = useState(69)
    const pre = "Pre"
    const post = "Post"
    const show = true
    return (
        <Fragment>
            <Col sm="12" md="6">
                <Card>
                    <CardHeader>
                        <H5 attrH5={{ className: "card-title" }}>Touchspin With Dropdown</H5><span>Use <code>data-bts-prefix & data-bts-postfix</code>attribute to set Prefix and Postfix to touchspin input with button.</span>
                    </CardHeader>
                    <CardBody>
                        <Commen val={val} setVal={setVal} pre={pre} post={post} show={show} />
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}
export default DropdownTouchspin