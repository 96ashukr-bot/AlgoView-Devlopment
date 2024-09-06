import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../../AbstractElements';
import ClipboardHighlight from './ClipboardHighlight';
import ClipboardPara from './ClipboardPara';
import ClipboardText from './ClipboardText';
import ClipboardTextarea from './ClipboardTextarea';


const FormClipboardContain = () => {
    return (
        <Fragment>
            <Breadcrumbs parent="Forms" title="Clipboard" subParent='Form Widgets' mainTitle="Clipboard" />
            <Container fluid={true}>
                <Row>
                    <ClipboardText />
                    <ClipboardTextarea />
                    <ClipboardPara />
                    <ClipboardHighlight />
                </Row>
            </Container>
        </Fragment>
    );
};
export default FormClipboardContain;