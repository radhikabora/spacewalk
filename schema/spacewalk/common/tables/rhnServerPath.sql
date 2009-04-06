--
-- Copyright (c) 2008 Red Hat, Inc.
--
-- This software is licensed to you under the GNU General Public License,
-- version 2 (GPLv2). There is NO WARRANTY for this software, express or
-- implied, including the implied warranties of MERCHANTABILITY or FITNESS
-- FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
-- along with this software; if not, see
-- http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
-- 
-- Red Hat trademarks are not licensed under GPLv2. No permission is
-- granted to use or replicate Red Hat trademarks that are incorporated
-- in this software or its documentation. 
--


CREATE TABLE rhnServerPath
(
    server_id        NUMBER NOT NULL 
                         CONSTRAINT rhn_serverpath_sid_fk
                             REFERENCES rhnServer (id), 
    proxy_server_id  NUMBER NOT NULL 
                         CONSTRAINT rhn_serverpath_psid_fk
                             REFERENCES rhnServer (id), 
    position         NUMBER NOT NULL, 
    hostname         VARCHAR2(256) NOT NULL, 
    created          DATE 
                         DEFAULT (sysdate) NOT NULL, 
    modified         DATE 
                         DEFAULT (sysdate) NOT NULL
)
ENABLE ROW MOVEMENT
;

CREATE UNIQUE INDEX rhn_serverpath_sid_pos_uq
    ON rhnServerPath (server_id, position)
    TABLESPACE [[2m_tbs]];

CREATE UNIQUE INDEX rhn_serverpath_psid_sid_uq
    ON rhnServerPath (proxy_server_id, server_id)
    TABLESPACE [[2m_tbs]];

