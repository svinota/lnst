from lnst.Controller.Task import ctl
from lnst.Controller.PerfRepoUtils import netperf_baseline_template
from lnst.Controller.PerfRepoUtils import netperf_result_template

from lnst.RecipeCommon.IRQ import pin_dev_irqs
from lnst.RecipeCommon.PerfRepo import generate_perfrepo_comment

# ------
# SETUP
# ------

mapping_file = ctl.get_alias("mapping_file")
perf_api = ctl.connect_PerfRepo(mapping_file)

product_name = ctl.get_alias("product_name")

m1 = ctl.get_host("testmachine1")
m2 = ctl.get_host("testmachine2")

m1.sync_resources(modules=["IcmpPing", "Icmp6Ping", "Netperf"])
m2.sync_resources(modules=["IcmpPing", "Icmp6Ping", "Netperf"])

# ------
# TESTS
# ------

vlans = ["vlan10", "vlan20", "vlan30"]
offloads = ["gro", "gso", "tso", "rx", "tx"]
offload_settings = [ [("gro", "on"), ("gso", "on"), ("tso", "on"), ("tx", "on"), ("rx", "on")],
                     [("gro", "off"), ("gso", "on"), ("tso", "on"), ("tx", "on"), ("rx", "on")],
                     [("gro", "on"), ("gso", "off"),  ("tso", "off"), ("tx", "on"), ("rx", "on")],
                     [("gro", "on"), ("gso", "on"), ("tso", "off"), ("tx", "off"), ("rx", "on")],
                     [("gro", "on"), ("gso", "on"), ("tso", "on"), ("tx", "on"), ("rx", "off")]]

ipv = ctl.get_alias("ipv")
mtu = ctl.get_alias("mtu")
netperf_duration = int(ctl.get_alias("netperf_duration"))
nperf_reserve = int(ctl.get_alias("nperf_reserve"))
nperf_confidence = ctl.get_alias("nperf_confidence")
nperf_max_runs = int(ctl.get_alias("nperf_max_runs"))
nperf_cpupin = ctl.get_alias("nperf_cpupin")
nperf_cpu_util = ctl.get_alias("nperf_cpu_util")
nperf_mode = ctl.get_alias("nperf_mode")
nperf_num_parallel = int(ctl.get_alias("nperf_num_parallel"))
nperf_debug = ctl.get_alias("nperf_debug")
pr_user_comment = ctl.get_alias("perfrepo_comment")

pr_comment = generate_perfrepo_comment([m1, m2], pr_user_comment)

m1_phy1 = m1.get_interface("eth1")
m1_phy1.set_mtu(mtu)
m2_phy1 = m2.get_interface("eth1")
m2_phy1.set_mtu(mtu)

for vlan in vlans:
    vlan_if1 = m1.get_interface(vlan)
    vlan_if1.set_mtu(mtu)
    vlan_if2 = m2.get_interface(vlan)
    vlan_if2.set_mtu(mtu)

if nperf_cpupin:
    m1.run("service irqbalance stop")
    m2.run("service irqbalance stop")

    # this will pin devices irqs to cpu #0
    for m, d in [ (m1, m1_phy1), (m2, m2_phy1) ]:
        pin_dev_irqs(m, d, 0)

ctl.wait(15)

ping_mod = ctl.get_module("IcmpPing",
                           options={
                               "count" : 100,
                               "interval" : 0.1
                           })
ping_mod6 = ctl.get_module("Icmp6Ping",
                           options={
                               "count" : 100,
                               "interval" : 0.1
                           })

m1_vlan1 = m1.get_interface(vlans[0])
m2_vlan1 = m2.get_interface(vlans[0])

p_opts = "-L %s" % (m2_vlan1.get_ip(0))
if nperf_cpupin and nperf_mode != "multi":
    p_opts += " -T%s,%s" % (nperf_cpupin, nperf_cpupin)

p_opts6 = "-L %s -6" % (m2_vlan1.get_ip(1))
if nperf_cpupin and nperf_mode != "multi":
    p_opts6 += " -T%s,%s" % (nperf_cpupin, nperf_cpupin)

netperf_srv = ctl.get_module("Netperf",
                              options={
                                  "role" : "server",
                                  "bind": m1_vlan1.get_ip(0)
                              })
netperf_srv6 = ctl.get_module("Netperf",
                              options={
                                  "role" : "server",
                                  "bind": m1_vlan1.get_ip(1),
                                  "netperf_opts" : " -6"
                              })
netperf_cli_tcp = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server": m1_vlan1.get_ip(0),
                                      "duration" : netperf_duration,
                                      "testname" : "TCP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts": p_opts,
                                      "debug" : nperf_debug
                                  })
netperf_cli_udp = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server": m1_vlan1.get_ip(0),
                                      "duration" : netperf_duration,
                                      "testname" : "UDP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts": p_opts,
                                      "debug" : nperf_debug
                                  })
netperf_cli_tcp6 = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server": m1_vlan1.get_ip(1),
                                      "duration" : netperf_duration,
                                      "testname" : "TCP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts": p_opts6,
                                      "debug" : nperf_debug
                                  })
netperf_cli_udp6 = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server": m1_vlan1.get_ip(1),
                                      "duration" : netperf_duration,
                                      "testname" : "UDP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts": p_opts6,
                                      "debug" : nperf_debug
                                  })

if nperf_mode == "multi":
    netperf_cli_tcp.unset_option("confidence")
    netperf_cli_udp.unset_option("confidence")
    netperf_cli_tcp6.unset_option("confidence")
    netperf_cli_udp6.unset_option("confidence")

    netperf_cli_tcp.update_options({"num_parallel": nperf_num_parallel})
    netperf_cli_udp.update_options({"num_parallel": nperf_num_parallel})
    netperf_cli_tcp6.update_options({"num_parallel": nperf_num_parallel})
    netperf_cli_udp6.update_options({"num_parallel": nperf_num_parallel})

for setting in offload_settings:
    #apply offload setting
    dev_features = ""
    for offload in setting:
        dev_features += " %s %s" % (offload[0], offload[1])

    m1.run("ethtool -K %s %s" % (m1_phy1.get_devname(),
                                 dev_features))
    m2.run("ethtool -K %s %s" % (m2_phy1.get_devname(),
                                 dev_features))
    if ("rx", "off") in setting:
        # when rx offload is turned off some of the cards might get reset
        # and link goes down, so wait a few seconds until NIC is ready
        ctl.wait(15)

    # Ping test
    for vlan1 in vlans:
        m1_vlan1 = m1.get_interface(vlan1)
        for vlan2 in vlans:
            m2_vlan2 = m2.get_interface(vlan2)

            ping_mod.update_options({"addr": m2_vlan2.get_ip(0),
                                     "iface": m1_vlan1.get_devname()})

            ping_mod6.update_options({"addr": m2_vlan2.get_ip(1),
                                      "iface": m1_vlan1.get_ip(1)})

            if vlan1 == vlan2:
                # These tests should pass
                # Ping between same VLANs
                if ipv in [ 'ipv4', 'both' ]:
                    m1.run(ping_mod)

                if ipv in [ 'ipv6', 'both' ]:
                    m1.run(ping_mod6)
            else:
                # These tests should fail
                # Ping across different VLAN
                if ipv in [ 'ipv4', 'both' ]:
                    m1.run(ping_mod, expect="fail")

    # Netperf test (both TCP and UDP)
    if ipv in [ 'ipv4', 'both' ]:
        srv_proc = m1.run(netperf_srv, bg=True)
        ctl.wait(2)

        # prepare PerfRepo result for tcp
        result_tcp = perf_api.new_result("tcp_ipv4_id",
                                         "tcp_ipv4_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_tcp.set_parameter(offload[0], offload[1])
        result_tcp.set_parameter('netperf_server_on_vlan', vlans[0])
        result_tcp.set_parameter('netperf_client_on_vlan', vlans[0])
        result_tcp.add_tag(product_name)
        if nperf_mode == "multi":
            result_tcp.add_tag("multithreaded")
            result_tcp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_tcp)
        netperf_baseline_template(netperf_cli_tcp, baseline)

        tcp_res_data = m2.run(netperf_cli_tcp,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_tcp, tcp_res_data)
        result_tcp.set_comment(pr_comment)
        perf_api.save_result(result_tcp)

        # prepare PerfRepo result for udp
        result_udp = perf_api.new_result("udp_ipv4_id",
                                         "udp_ipv4_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_udp.set_parameter(offload[0], offload[1])
        result_udp.set_parameter('netperf_server_on_vlan', vlans[0])
        result_udp.set_parameter('netperf_client_on_vlan', vlans[0])
        result_udp.add_tag(product_name)
        if nperf_mode == "multi":
            result_udp.add_tag("multithreaded")
            result_udp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_udp)
        netperf_baseline_template(netperf_cli_udp, baseline)

        udp_res_data = m2.run(netperf_cli_udp,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_udp, udp_res_data)
        result_udp.set_comment(pr_comment)
        perf_api.save_result(result_udp)

        srv_proc.intr()

    if ipv in [ 'ipv6', 'both' ]:
        srv_proc = m1.run(netperf_srv6, bg=True)
        ctl.wait(2)

        # prepare PerfRepo result for tcp ipv6
        result_tcp = perf_api.new_result("tcp_ipv6_id",
                                         "tcp_ipv6_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_tcp.set_parameter(offload[0], offload[1])
        result_tcp.set_parameter('netperf_server_on_vlan', vlans[0])
        result_tcp.set_parameter('netperf_client_on_vlan', vlans[0])
        result_tcp.set_tag(product_name)
        if nperf_mode == "multi":
            result_tcp.add_tag("multithreaded")
            result_tcp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_tcp)
        netperf_baseline_template(netperf_cli_tcp6, baseline)

        tcp_res_data = m2.run(netperf_cli_tcp6,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_tcp, tcp_res_data)
        result_tcp.set_comment(pr_comment)
        perf_api.save_result(result_tcp)

        # prepare PerfRepo result for udp ipv6
        result_udp = perf_api.new_result("udp_ipv6_id",
                                         "udp_ipv6_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_udp.set_parameter(offload[0], offload[1])
        result_udp.set_parameter('netperf_server_on_vlan', vlans[0])
        result_udp.set_parameter('netperf_client_on_vlan', vlans[0])
        result_udp.set_tag(product_name)
        if nperf_mode == "multi":
            result_udp.add_tag("multithreaded")
            result_udp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_udp)
        netperf_baseline_template(netperf_cli_udp6, baseline)

        udp_res_data = m2.run(netperf_cli_udp6,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_udp, udp_res_data)
        result_udp.set_comment(pr_comment)
        perf_api.save_result(result_udp)

        srv_proc.intr()

#reset offload states
dev_features = ""
for offload in offloads:
    dev_features += " %s %s" % (offload, "on")
m1.run("ethtool -K %s %s" % (m1_phy1.get_devname(), dev_features))
m2.run("ethtool -K %s %s" % (m2_phy1.get_devname(), dev_features))

if nperf_cpupin:
    m1.run("service irqbalance start")
    m2.run("service irqbalance start")
