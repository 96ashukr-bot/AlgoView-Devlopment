import React, { useEffect, useMemo, useState } from 'react';
import { Button, Card, CardBody, Col, Container, Form, FormGroup, Input, Label, Modal, ModalBody, ModalFooter, ModalHeader, Row, Table } from 'reactstrap';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import {
  assignExecutionNodeToClient,
  createExecutionNode,
  getClients,
  getExecutionNodes,
  releaseExecutionNodeFromClient,
  updateExecutionNode,
  verifyExecutionNodeProxy,
} from '../../../Services/Authentication';

const blankForm = {
  name: '',
  execution_type: 'proxy',
  ip_address: '',
  provider: '',
  server_url: '',
  node_id: '',
  node_secret: '',
  proxy_protocol: 'http',
  proxy_host: '',
  proxy_port: '',
  proxy_username: '',
  proxy_password: '',
  is_active: true,
  is_verified_with_broker: true,
};

const IPPool = ({ mode = 'unassigned' }) => {
  const [nodes, setNodes] = useState([]);
  const [clients, setClients] = useState([]);
  const [form, setForm] = useState(blankForm);
  const [clientByNode, setClientByNode] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingNode, setEditingNode] = useState(null);
  const [editForm, setEditForm] = useState(blankForm);

  const pageTitle = mode === 'create' ? 'Create IP' : mode === 'assigned' ? 'Assigned IP' : 'Unassigned IP';
  const isCreateMode = mode === 'create';

  useEffect(() => {
    fetchNodes();
    fetchClients();
  }, []);

  const fetchNodes = async () => {
    setLoading(true);
    try {
      const response = await getExecutionNodes();
      setNodes(response?.results || []);
    } catch (error) {
      toast.error(error.message || 'Failed to fetch IP pool.');
    } finally {
      setLoading(false);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await getClients(1, 1000);
      setClients(response?.results || []);
    } catch (error) {
      console.error('Error fetching clients for IP assignment:', error);
    }
  };

  const filteredNodes = useMemo(() => {
    if (mode === 'assigned') {
      return nodes.filter((node) => node.assigned_client);
    }
    if (mode === 'unassigned') {
      return nodes.filter((node) => !node.assigned_client);
    }
    return nodes;
  }, [mode, nodes]);

  const stats = useMemo(() => {
    const assigned = nodes.filter((node) => node.assigned_client).length;
    return {
      total: nodes.length,
      assigned,
      unassigned: nodes.length - assigned,
    };
  }, [nodes]);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((previous) => ({
      ...previous,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const validateNodeForm = (values, { requireSecrets = true } = {}) => {
    const isProxy = values.execution_type === 'proxy';
    const requiredFields = isProxy
      ? ['name', 'ip_address', 'proxy_protocol', 'proxy_host', 'proxy_port']
      : ['name', 'ip_address', 'server_url', 'node_id', ...(requireSecrets ? ['node_secret'] : [])];
    return requiredFields.find((field) => !String(values[field] || '').trim());
  };

  const buildNodePayload = (values, { includeSecrets = true } = {}) => {
    const isProxy = values.execution_type === 'proxy';
    const payload = {
      name: values.name.trim(),
      execution_type: values.execution_type,
      ip_address: values.ip_address.trim(),
      provider: values.provider.trim(),
      is_active: values.is_active,
      is_verified_with_broker: values.is_verified_with_broker,
    };
    if (isProxy) {
      payload.proxy_protocol = values.proxy_protocol;
      payload.proxy_host = values.proxy_host.trim();
      payload.proxy_port = values.proxy_port;
      payload.proxy_username = values.proxy_username.trim();
      if (includeSecrets && values.proxy_password) {
        payload.proxy_password = values.proxy_password;
      }
      payload.server_url = null;
      payload.node_id = null;
    } else {
      payload.server_url = values.server_url.trim();
      payload.node_id = values.node_id.trim();
      if (includeSecrets && values.node_secret) {
        payload.node_secret = values.node_secret;
      }
      payload.proxy_protocol = null;
      payload.proxy_host = null;
      payload.proxy_port = null;
      payload.proxy_username = null;
    }
    return payload;
  };

  const handleCreate = async () => {
    const missingField = validateNodeForm(form);
    if (missingField) {
      toast.error('Please fill all required IP details.');
      return;
    }

    setSaving(true);
    try {
      const payload = { ...buildNodePayload(form), status: 'free' };

      await createExecutionNode(payload);
      toast.success('IP saved in unassigned pool.');
      setForm(blankForm);
      fetchNodes();
    } catch (error) {
      toast.error(error.message || 'Failed to create IP.');
    } finally {
      setSaving(false);
    }
  };

  const openEditModal = (node) => {
    setEditingNode(node);
    setEditForm({
      ...blankForm,
      name: node.name || '',
      execution_type: node.execution_type || 'proxy',
      ip_address: node.ip_address || '',
      provider: node.provider || '',
      server_url: node.server_url || '',
      node_id: node.node_id || '',
      node_secret: '',
      proxy_protocol: node.proxy_protocol || 'http',
      proxy_host: node.proxy_host || '',
      proxy_port: node.proxy_port || '',
      proxy_username: node.proxy_username || '',
      proxy_password: '',
      is_active: Boolean(node.is_active),
      is_verified_with_broker: Boolean(node.is_verified_with_broker),
    });
  };

  const closeEditModal = () => {
    setEditingNode(null);
    setEditForm(blankForm);
  };

  const handleEditChange = (event) => {
    const { name, value, type, checked } = event.target;
    setEditForm((previous) => ({
      ...previous,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleUpdate = async () => {
    if (!editingNode) {
      return;
    }
    const missingField = validateNodeForm(editForm, { requireSecrets: false });
    if (missingField) {
      toast.error('Please fill all required IP details.');
      return;
    }

    setSaving(true);
    try {
      await updateExecutionNode(editingNode.id, buildNodePayload(editForm));
      toast.success('IP details updated.');
      closeEditModal();
      fetchNodes();
    } catch (error) {
      toast.error(error.message || 'Failed to update IP.');
    } finally {
      setSaving(false);
    }
  };

  const handleAssign = async (nodeId) => {
    const clientId = clientByNode[nodeId];
    if (!clientId) {
      toast.error('Please select a client first.');
      return;
    }
    try {
      await assignExecutionNodeToClient(clientId, nodeId);
      toast.success('IP assigned to client.');
      setClientByNode((previous) => ({ ...previous, [nodeId]: '' }));
      fetchNodes();
    } catch (error) {
      toast.error(error.message || 'Failed to assign IP.');
    }
  };

  const handleRelease = async (node) => {
    if (!node.assigned_client) {
      return;
    }
    try {
      await releaseExecutionNodeFromClient(node.assigned_client);
      toast.success('IP released to unassigned pool.');
      fetchNodes();
    } catch (error) {
      toast.error(error.message || 'Failed to release IP.');
    }
  };

  const handleVerify = async (nodeId) => {
    try {
      const response = await verifyExecutionNodeProxy(nodeId);
      toast.success(response?.result?.message || 'Proxy verification completed.');
      fetchNodes();
    } catch (error) {
      toast.error(error.message || 'Failed to verify proxy.');
    }
  };

  const renderCreateForm = () => (
    <Card>
      <CardBody>
        <Form>
          <Row>
            <Col md="3">
              <FormGroup>
                <Label>Execution Type *</Label>
                <Input type="select" name="execution_type" value={form.execution_type} onChange={handleChange}>
                  <option value="proxy">Proxy IP</option>
                  <option value="vps_node">VPS Node</option>
                </Input>
              </FormGroup>
            </Col>
            <Col md="3">
              <FormGroup>
                <Label>Name *</Label>
                <Input name="name" value={form.name} onChange={handleChange} placeholder="Alice Proxy Mumbai 1" />
              </FormGroup>
            </Col>
            <Col md="3">
              <FormGroup>
                <Label>Static IP *</Label>
                <Input name="ip_address" value={form.ip_address} onChange={handleChange} placeholder="203.0.113.10" />
              </FormGroup>
            </Col>
            <Col md="3">
              <FormGroup>
                <Label>Provider</Label>
                <Input name="provider" value={form.provider} onChange={handleChange} placeholder="AWS / Proxy vendor" />
              </FormGroup>
            </Col>
          </Row>

          {form.execution_type === 'proxy' ? (
            <>
              <Row>
                <Col md="3">
                  <FormGroup>
                    <Label>Proxy Protocol *</Label>
                    <Input type="select" name="proxy_protocol" value={form.proxy_protocol} onChange={handleChange}>
                      <option value="http">HTTP</option>
                      <option value="https">HTTPS</option>
                      <option value="socks5">SOCKS5</option>
                    </Input>
                  </FormGroup>
                </Col>
                <Col md="4">
                  <FormGroup>
                    <Label>Proxy Host *</Label>
                    <Input name="proxy_host" value={form.proxy_host} onChange={handleChange} placeholder="proxy.vendor.com" />
                  </FormGroup>
                </Col>
                <Col md="2">
                  <FormGroup>
                    <Label>Proxy Port *</Label>
                    <Input name="proxy_port" value={form.proxy_port} onChange={handleChange} placeholder="8080" />
                  </FormGroup>
                </Col>
                <Col md="3">
                  <FormGroup>
                    <Label>Proxy Username</Label>
                    <Input name="proxy_username" value={form.proxy_username} onChange={handleChange} autoComplete="off" />
                  </FormGroup>
                </Col>
              </Row>
              <Row>
                <Col md="4">
                  <FormGroup>
                    <Label>Proxy Password</Label>
                    <Input type="password" name="proxy_password" value={form.proxy_password} onChange={handleChange} autoComplete="off" />
                  </FormGroup>
                </Col>
              </Row>
            </>
          ) : (
            <Row>
              <Col md="4">
                <FormGroup>
                  <Label>Node ID *</Label>
                  <Input name="node_id" value={form.node_id} onChange={handleChange} placeholder="client-node-1" />
                </FormGroup>
              </Col>
              <Col md="4">
                <FormGroup>
                  <Label>Server URL *</Label>
                  <Input name="server_url" value={form.server_url} onChange={handleChange} placeholder="https://node.example.com" />
                </FormGroup>
              </Col>
              <Col md="4">
                <FormGroup>
                  <Label>Node Secret *</Label>
                  <Input type="password" name="node_secret" value={form.node_secret} onChange={handleChange} />
                </FormGroup>
              </Col>
            </Row>
          )}

          <Row className="align-items-center">
            <Col md="3">
              <FormGroup check>
                <Input type="checkbox" name="is_active" checked={form.is_active} onChange={handleChange} />
                <Label check>Active</Label>
              </FormGroup>
            </Col>
            <Col md="3">
              <FormGroup check>
                <Input type="checkbox" name="is_verified_with_broker" checked={form.is_verified_with_broker} onChange={handleChange} />
                <Label check>Broker IP verified</Label>
              </FormGroup>
            </Col>
            <Col md="6" className="text-end">
              <Button className="search-btn-clr" onClick={handleCreate} disabled={saving}>
                {saving ? 'Saving...' : 'Create IP'}
              </Button>
            </Col>
          </Row>
        </Form>
      </CardBody>
    </Card>
  );

  const renderList = () => (
    <Card>
      <CardBody>
        <div style={{ overflowX: 'auto' }}>
          <Table bordered hover responsive>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Static IP</th>
                <th>Provider</th>
                <th>Status</th>
                <th>Proxy Check</th>
                <th>Assigned Client</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredNodes.length > 0 ? (
                filteredNodes.map((node) => (
                  <tr key={node.id}>
                    <td>{node.name || '-'}</td>
                    <td>{node.execution_type === 'proxy' ? 'Proxy' : 'VPS'}</td>
                    <td>{node.ip_address || '-'}</td>
                    <td>{node.provider || '-'}</td>
                    <td>{node.status || '-'}{node.is_active ? '' : ' / inactive'}{node.is_verified_with_broker ? ' / broker verified' : ' / broker pending'}</td>
                    <td>
                      {node.execution_type === 'proxy' ? (
                        <>
                          <div>{node.proxy_public_ip_verified ? 'Verified' : 'Not verified'}</div>
                          {node.proxy_last_seen_ip && <small style={{ color: '#6b7280' }}>{node.proxy_last_seen_ip}</small>}
                        </>
                      ) : 'Not applicable'}
                    </td>
                    <td>{node.assigned_client_email || (node.assigned_client ? `Client #${node.assigned_client}` : 'Unassigned')}</td>
                    <td>
                      <div className="d-flex" style={{ gap: '8px', flexWrap: 'wrap', minWidth: '260px' }}>
                        {node.execution_type === 'proxy' && (
                          <Button size="sm" color="secondary" outline onClick={() => handleVerify(node.id)}>
                            Verify
                          </Button>
                        )}
                        <Button size="sm" color="primary" outline onClick={() => openEditModal(node)}>
                          Edit
                        </Button>
                        {node.assigned_client ? (
                          <Button size="sm" color="danger" outline onClick={() => handleRelease(node)}>
                            Release
                          </Button>
                        ) : (
                          <>
                            <Input
                              type="select"
                              bsSize="sm"
                              value={clientByNode[node.id] || ''}
                              onChange={(event) => setClientByNode((previous) => ({ ...previous, [node.id]: event.target.value }))}
                              style={{ width: '150px' }}
                            >
                              <option value="">Select client</option>
                              {clients.map((client) => (
                                <option key={client.id} value={client.id}>
                                  {client.fullName || client.email || `Client #${client.id}`}
                                </option>
                              ))}
                            </Input>
                            <Button size="sm" className="search-btn-clr" onClick={() => handleAssign(node.id)}>
                              Assign
                            </Button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" className="text-center">{loading ? 'Loading IP pool...' : 'No IPs found.'}</td>
                </tr>
              )}
            </tbody>
          </Table>
        </div>
      </CardBody>
    </Card>
  );

  return (
    <Container fluid>
      <ToastContainer />
      <Row>
        <Col sm="12">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <div>
              <h3 className="mb-1">IP Pool - {pageTitle}</h3>
              <p className="mb-0" style={{ color: '#6b7280' }}>
                Total {stats.total} | Assigned {stats.assigned} | Unassigned {stats.unassigned}
              </p>
            </div>
          </div>
          {isCreateMode ? renderCreateForm() : renderList()}
        </Col>
      </Row>
      <Modal isOpen={Boolean(editingNode)} toggle={closeEditModal} size="lg">
        <ModalHeader toggle={closeEditModal}>Edit IP Details</ModalHeader>
        <ModalBody>
          <Form>
            <Row>
              <Col md="3">
                <FormGroup>
                  <Label>Execution Type *</Label>
                  <Input type="select" name="execution_type" value={editForm.execution_type} onChange={handleEditChange}>
                    <option value="proxy">Proxy IP</option>
                    <option value="vps_node">VPS Node</option>
                  </Input>
                </FormGroup>
              </Col>
              <Col md="3">
                <FormGroup>
                  <Label>Name *</Label>
                  <Input name="name" value={editForm.name} onChange={handleEditChange} />
                </FormGroup>
              </Col>
              <Col md="3">
                <FormGroup>
                  <Label>Static IP *</Label>
                  <Input name="ip_address" value={editForm.ip_address} onChange={handleEditChange} />
                </FormGroup>
              </Col>
              <Col md="3">
                <FormGroup>
                  <Label>Provider</Label>
                  <Input name="provider" value={editForm.provider} onChange={handleEditChange} />
                </FormGroup>
              </Col>
            </Row>

            {editForm.execution_type === 'proxy' ? (
              <>
                <Row>
                  <Col md="3">
                    <FormGroup>
                      <Label>Proxy Protocol *</Label>
                      <Input type="select" name="proxy_protocol" value={editForm.proxy_protocol} onChange={handleEditChange}>
                        <option value="http">HTTP</option>
                        <option value="https">HTTPS</option>
                        <option value="socks5">SOCKS5</option>
                      </Input>
                    </FormGroup>
                  </Col>
                  <Col md="4">
                    <FormGroup>
                      <Label>Proxy Host *</Label>
                      <Input name="proxy_host" value={editForm.proxy_host} onChange={handleEditChange} />
                    </FormGroup>
                  </Col>
                  <Col md="2">
                    <FormGroup>
                      <Label>Proxy Port *</Label>
                      <Input name="proxy_port" value={editForm.proxy_port} onChange={handleEditChange} />
                    </FormGroup>
                  </Col>
                  <Col md="3">
                    <FormGroup>
                      <Label>Proxy Username</Label>
                      <Input name="proxy_username" value={editForm.proxy_username} onChange={handleEditChange} autoComplete="off" />
                    </FormGroup>
                  </Col>
                </Row>
                <Row>
                  <Col md="4">
                    <FormGroup>
                      <Label>Proxy Password</Label>
                      <Input type="password" name="proxy_password" value={editForm.proxy_password} onChange={handleEditChange} autoComplete="off" placeholder="Leave blank to keep current" />
                    </FormGroup>
                  </Col>
                </Row>
              </>
            ) : (
              <Row>
                <Col md="4">
                  <FormGroup>
                    <Label>Node ID *</Label>
                    <Input name="node_id" value={editForm.node_id} onChange={handleEditChange} />
                  </FormGroup>
                </Col>
                <Col md="4">
                  <FormGroup>
                    <Label>Server URL *</Label>
                    <Input name="server_url" value={editForm.server_url} onChange={handleEditChange} />
                  </FormGroup>
                </Col>
                <Col md="4">
                  <FormGroup>
                    <Label>Node Secret</Label>
                    <Input type="password" name="node_secret" value={editForm.node_secret} onChange={handleEditChange} placeholder="Leave blank to keep current" />
                  </FormGroup>
                </Col>
              </Row>
            )}

            <Row>
              <Col md="3">
                <FormGroup check>
                  <Input type="checkbox" name="is_active" checked={editForm.is_active} onChange={handleEditChange} />
                  <Label check>Active</Label>
                </FormGroup>
              </Col>
              <Col md="3">
                <FormGroup check>
                  <Input type="checkbox" name="is_verified_with_broker" checked={editForm.is_verified_with_broker} onChange={handleEditChange} />
                  <Label check>Broker IP verified</Label>
                </FormGroup>
              </Col>
            </Row>
          </Form>
        </ModalBody>
        <ModalFooter>
          <Button color="secondary" outline onClick={closeEditModal} disabled={saving}>Cancel</Button>
          <Button className="search-btn-clr" onClick={handleUpdate} disabled={saving}>
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </ModalFooter>
      </Modal>
    </Container>
  );
};

export default IPPool;
