
def divide_dss_multi_binary(dss, binary_ds_names):
     binaries, multis = [], []
     for dn in dss:
          is_binary = False
          for bn in binary_ds_names:
               if bn in dn:
                    is_binary = True
                    break
          if is_binary: binaries.append(dn)
          else: multis.append(dn)
     return binaries, multis