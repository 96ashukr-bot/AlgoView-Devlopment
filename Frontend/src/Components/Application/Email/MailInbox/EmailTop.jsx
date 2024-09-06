import React, { Fragment, useContext, useState } from 'react';
import { Col, Dropdown, DropdownItem, DropdownMenu, DropdownToggle, Row } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';
import { Draft, More, Spam, Trash } from '../../../../Constant';
import EmailContext from '../../../../_helper/Email';

const EmailTopToggle = ({ selectedFav, moreCallBack }) => {
    const { type } = useContext(EmailContext);

    const [dropdownOpen, setOpen] = useState(false);
    const toggle = () => setOpen(!dropdownOpen);

    return (
        <Fragment>
            <div className="email-top">
                <Row>
                    <Col>
                        <H5>{selectedFav ? 'Favourite' : type}</H5>
                    </Col>
                    <Col className="text-end">
                        <div className="dropdown">
                            <Dropdown isOpen={dropdownOpen} toggle={toggle}>
                                <DropdownToggle className="dropbtn" color="primary" caret> {More} </DropdownToggle>
                                <DropdownMenu>
                                    <DropdownItem onClick={() => moreCallBack("Draft")}>{Draft}</DropdownItem>
                                    <DropdownItem onClick={() => moreCallBack("Trash")}>{Trash}</DropdownItem>
                                    <DropdownItem onClick={() => moreCallBack("Spam")}>{Spam}</DropdownItem>
                                </DropdownMenu>
                            </Dropdown>
                        </div>
                    </Col>
                </Row>
            </div>
        </Fragment>
    )
}

export default EmailTopToggle;