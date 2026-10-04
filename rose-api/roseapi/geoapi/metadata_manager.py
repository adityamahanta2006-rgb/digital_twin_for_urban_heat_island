import json
import os
from django.http import JsonResponse
from geoapi import models as geoapi_models
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class FileStorageMetadata(models.Model):
    path = models.CharField(
        _("Location of the dataset in the shared folder"), 
        primary_key=True,
        max_length=400, 
        null=False, 
        default=f'{getattr(settings, "PROCESSING_STORAGE_DIR", "")}'
    )
    dataset_name = models.CharField(_("Name of the dataset"), max_length=50, null=False) 

    def __str__(self):
        return "File Storage Metadata"

@csrf_exempt
@require_http_methods(["PUT"])
def update_file_metadata(request):
    if request.method == "PUT":

        # from the shared data folder, obtain all the metadata elements recursively.
        metadata_entries = []
        data_dir = getattr(settings, "PROCESSING_STORAGE_DIR", None)
        if data_dir is None: 
            raise Exception("No data directory")
        try:
            for dirpath, dirnames, filenames in os.walk(data_dir):
                for filename in filenames:
                    print(filename)
                    if filename.endswith(".metadata"):
                        file_path = os.path.join(dirpath, filename)
                        try:
                            with open(file_path, "r", encoding="utf-8") as fh:
                                parsed = json.load(fh)
                            
                        except Exception:
                            # skip files that can't be opened or parsed
                            continue
                            
                        metadata_entries.append({"path": parsed["location"], "dataset_name": parsed["name"]})
        except: 
            raise Exception("Error reading metadata files")
        
        # create or update records for each discovered metadata entry
        for entry in metadata_entries:
            path = entry.get("path")
            dataset_name = entry.get("dataset_name")
            if not path or not dataset_name:
                continue
            FileStorageMetadata.objects.update_or_create(
                path=path,
                defaults={"dataset_name": dataset_name}
            )
        
        print(metadata_entries)

        
        return JsonResponse({"status": "success", "message": "Metadata updated successfully."})

    else:
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


        

    

    
