import React, { Fragment, useState } from "react";
import { Card, CardBody, CardHeader, Col, Container, Row } from "reactstrap";
import { SelectSingleImageUpload } from '../../../Constant';
import { Breadcrumbs, Btn, Image } from '../../../AbstractElements';
import Files from 'react-files';

const UploadImage = () => {
    const [files, setFiles] = useState([]);

    function deleteFile(e) {
        setFiles([]);
        return files

    }
    const onFilesChange = (files) => {
        setFiles(files)
    }
    const onFilesError = (error, file) => {
        setFiles(file)
    }

    return (
        <Fragment>
            <Breadcrumbs mainTitle="Image Upload" parent="Bouns Ui" title="Uploads" />
            <Container fluid={true}>
                <Row>
                    <Col sm="12">
                        <Card>
                            <CardHeader>
                                <h5>{SelectSingleImageUpload}</h5>
                            </CardHeader>
                            <CardBody className="fileUploader">
                                <Files
                                    className='files-dropzone fileContainer'
                                    onChange={onFilesChange}
                                    onError={onFilesError}
                                    accepts={['image/*']}
                                    multiple={false}
                                    maxFileSize={10000000}
                                    minFileSize={0}
                                    clickable
                                >
                                    {
                                        files.length > 0
                                            ? <div className='files-gallery'>
                                                {files.map((file, index) =>
                                                    <div key={index}>
                                                        <Image attrImage={{ className: 'files-gallery-item', alt: "img", src: `${file.preview.url}` }} />
                                                    </div>
                                                )}
                                            </div>

                                            : <div className="d-flex justify-content-center">
                                                <Btn attrBtn={{ className: "mt-2", type: "button", color: 'primary' }} >Upload Image</Btn>
                                            </div>
                                    }
                                </Files>
                                {files.length > 0 ?
                                    <div className="d-flex justify-content-center">
                                        <Btn attrBtn={{ className: "mt-2", color: 'danger', type: "button", onClick: () => deleteFile(files) }} >
                                            Delete
                                        </Btn></div> : ''}

                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>

    );
};

export default UploadImage;